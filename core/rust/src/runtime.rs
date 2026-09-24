use crate::error::CoreError;
use crate::ids::{AgentId, BehaviorId};
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RuntimeState {
    Created,
    Running,
    Paused,
    Stopped,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentState {
    Created,
    Ready,
    Running,
    Paused,
    Stopped,
}

#[derive(Debug, Clone)]
pub struct Behavior {
    id: BehaviorId,
}

impl Behavior {
    pub fn new(id: BehaviorId) -> Self {
        Self { id }
    }

    pub fn id(&self) -> &BehaviorId {
        &self.id
    }
}

#[derive(Debug, Clone)]
pub struct Agent {
    id: AgentId,
    state: AgentState,
    behaviors: HashMap<String, Behavior>,
}

impl Agent {
    pub fn new(id: AgentId) -> Self {
        Self {
            id,
            state: AgentState::Created,
            behaviors: HashMap::new(),
        }
    }

    pub fn id(&self) -> &AgentId {
        &self.id
    }

    pub fn state(&self) -> AgentState {
        self.state
    }

    pub fn register_behavior(&mut self, behavior_id: BehaviorId) -> Result<(), CoreError> {
        let key = behavior_id.as_str().to_owned();

        if self.behaviors.contains_key(&key) {
            return Err(CoreError::BehaviorAlreadyExists {
                behavior: key,
            });
        }

        self.behaviors.insert(key, Behavior::new(behavior_id));

        if self.state == AgentState::Created {
            self.state = AgentState::Ready;
        }

        Ok(())
    }

    pub fn has_behavior(&self, behavior_id: &BehaviorId) -> bool {
        self.behaviors.contains_key(behavior_id.as_str())
    }

    pub fn start(&mut self) -> Result<(), CoreError> {
        match self.state {
            AgentState::Created | AgentState::Ready | AgentState::Paused => {
                self.state = AgentState::Running;
                Ok(())
            }
            AgentState::Running => Ok(()),
            AgentState::Stopped => Err(CoreError::InvalidState {
                message: "Stopped agents cannot be started.".to_owned(),
            }),
        }
    }

    pub fn pause(&mut self) -> Result<(), CoreError> {
        match self.state {
            AgentState::Running => {
                self.state = AgentState::Paused;
                Ok(())
            }
            AgentState::Paused => Ok(()),
            _ => Err(CoreError::InvalidState {
                message: "Only running agents can be paused.".to_owned(),
            }),
        }
    }

    pub fn stop(&mut self) -> Result<(), CoreError> {
        match self.state {
            AgentState::Stopped => Ok(()),
            _ => {
                self.state = AgentState::Stopped;
                Ok(())
            }
        }
    }
}

#[derive(Debug)]
pub struct CardinalRuntime {
    state: RuntimeState,
    agents: HashMap<String, Agent>,
}

impl Default for CardinalRuntime {
    fn default() -> Self {
        Self::new()
    }
}

impl CardinalRuntime {
    pub fn new() -> Self {
        Self {
            state: RuntimeState::Created,
            agents: HashMap::new(),
        }
    }

    pub fn state(&self) -> RuntimeState {
        self.state
    }

    pub fn register_agent(&mut self, agent: Agent) -> Result<(), CoreError> {
        let key = agent.id().as_str().to_owned();

        if self.agents.contains_key(&key) {
            return Err(CoreError::AgentAlreadyExists { agent: key });
        }

        self.agents.insert(key, agent);

        Ok(())
    }

    pub fn get_agent(&self, id: &AgentId) -> Result<&Agent, CoreError> {
        self.agents
            .get(id.as_str())
            .ok_or_else(|| CoreError::AgentNotFound {
                agent: id.as_str().to_owned(),
            })
    }

    pub fn get_agent_mut(&mut self, id: &AgentId) -> Result<&mut Agent, CoreError> {
        self.agents
            .get_mut(id.as_str())
            .ok_or_else(|| CoreError::AgentNotFound {
                agent: id.as_str().to_owned(),
            })
    }

    pub fn start(&mut self) -> Result<(), CoreError> {
        match self.state {
            RuntimeState::Created | RuntimeState::Paused => {
                self.state = RuntimeState::Running;
                Ok(())
            }
            RuntimeState::Running => Ok(()),
            RuntimeState::Stopped => Err(CoreError::InvalidState {
                message: "Stopped runtime cannot be started.".to_owned(),
            }),
        }
    }

    pub fn pause(&mut self) -> Result<(), CoreError> {
        match self.state {
            RuntimeState::Running => {
                self.state = RuntimeState::Paused;
                Ok(())
            }
            RuntimeState::Paused => Ok(()),
            _ => Err(CoreError::InvalidState {
                message: "Only running runtime can be paused.".to_owned(),
            }),
        }
    }

    pub fn stop(&mut self) -> Result<(), CoreError> {
        match self.state {
            RuntimeState::Stopped => Ok(()),
            _ => {
                self.state = RuntimeState::Stopped;

                for agent in self.agents.values_mut() {
                    let _ = agent.stop();
                }

                Ok(())
            }
        }
    }

    pub fn start_agent(&mut self, id: &AgentId) -> Result<(), CoreError> {
        if self.state != RuntimeState::Running {
            return Err(CoreError::InvalidState {
                message: "Runtime must be running before an agent can start.".to_owned(),
            });
        }

        let agent = self.get_agent_mut(id)?;
        agent.start()
    }

    pub fn stop_agent(&mut self, id: &AgentId) -> Result<(), CoreError> {
        let agent = self.get_agent_mut(id)?;
        agent.stop()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ids::{AgentId, BehaviorId};

    #[test]
    fn runtime_starts_in_created_state() {
        let runtime = CardinalRuntime::new();
        assert_eq!(runtime.state(), RuntimeState::Created);
    }

    #[test]
    fn runtime_can_start() {
        let mut runtime = CardinalRuntime::new();

        runtime.start().unwrap();

        assert_eq!(runtime.state(), RuntimeState::Running);
    }

    #[test]
    fn runtime_can_pause() {
        let mut runtime = CardinalRuntime::new();

        runtime.start().unwrap();
        runtime.pause().unwrap();

        assert_eq!(runtime.state(), RuntimeState::Paused);
    }

    #[test]
    fn runtime_can_stop() {
        let mut runtime = CardinalRuntime::new();

        runtime.start().unwrap();
        runtime.stop().unwrap();

        assert_eq!(runtime.state(), RuntimeState::Stopped);
    }

    #[test]
    fn agent_can_be_registered() {
        let mut runtime = CardinalRuntime::new();
        let agent = Agent::new(AgentId::new("test-agent").unwrap());

        runtime.register_agent(agent).unwrap();

        let id = AgentId::new("test-agent").unwrap();
        assert_eq!(runtime.get_agent(&id).unwrap().state(), AgentState::Created);
    }

    #[test]
    fn duplicate_agent_is_rejected() {
        let mut runtime = CardinalRuntime::new();
        let agent = Agent::new(AgentId::new("test-agent").unwrap());
        let duplicate = Agent::new(AgentId::new("test-agent").unwrap());

        runtime.register_agent(agent).unwrap();

        assert!(matches!(
            runtime.register_agent(duplicate),
            Err(CoreError::AgentAlreadyExists { .. })
        ));
    }

    #[test]
    fn agent_can_register_behavior() {
        let mut agent = Agent::new(AgentId::new("agent").unwrap());

        agent
            .register_behavior(BehaviorId::new("tick").unwrap())
            .unwrap();

        assert!(agent.has_behavior(&BehaviorId::new("tick").unwrap()));
        assert_eq!(agent.state(), AgentState::Ready);
    }

    #[test]
    fn agent_can_start() {
        let mut runtime = CardinalRuntime::new();
        runtime
            .register_agent(Agent::new(AgentId::new("agent").unwrap()))
            .unwrap();

        runtime.start().unwrap();

        let id = AgentId::new("agent").unwrap();
        runtime.start_agent(&id).unwrap();

        assert_eq!(
            runtime.get_agent(&id).unwrap().state(),
            AgentState::Running
        );
    }

    #[test]
    fn agent_cannot_start_before_runtime() {
        let mut runtime = CardinalRuntime::new();
        runtime
            .register_agent(Agent::new(AgentId::new("agent").unwrap()))
            .unwrap();

        let id = AgentId::new("agent").unwrap();

        assert!(matches!(
            runtime.start_agent(&id),
            Err(CoreError::InvalidState { .. })
        ));
    }

    #[test]
    fn stopping_runtime_stops_agents() {
        let mut runtime = CardinalRuntime::new();

        runtime
            .register_agent(Agent::new(AgentId::new("agent").unwrap()))
            .unwrap();

        runtime.start().unwrap();

        let id = AgentId::new("agent").unwrap();
        runtime.start_agent(&id).unwrap();
        runtime.stop().unwrap();

        assert_eq!(
            runtime.get_agent(&id).unwrap().state(),
            AgentState::Stopped
        );
    }
}
