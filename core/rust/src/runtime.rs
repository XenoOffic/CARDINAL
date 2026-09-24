use std::collections::{HashMap, HashSet};

use crate::error::CoreError;
use crate::ids::{AgentId, BehaviorId};

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
pub struct Agent {
    id: AgentId,
    state: AgentState,
    behaviors: HashSet<BehaviorId>,
}

impl Agent {
    pub fn new(id: AgentId) -> Self {
        Self {
            id,
            state: AgentState::Created,
            behaviors: HashSet::new(),
        }
    }

    pub fn id(&self) -> &AgentId {
        &self.id
    }

    pub fn state(&self) -> AgentState {
        self.state
    }

    pub fn register_behavior(
        &mut self,
        behavior: BehaviorId,
    ) -> Result<(), CoreError> {
        if !self.behaviors.insert(behavior.clone()) {
            return Err(
                CoreError::BehaviorAlreadyExists {
                    behavior: behavior.as_str().to_string(),
                },
            );
        }

        if self.state == AgentState::Created {
            self.state = AgentState::Ready;
        }

        Ok(())
    }

    pub fn has_behavior(
        &self,
        behavior: &BehaviorId,
    ) -> bool {
        self.behaviors.contains(behavior)
    }

    pub fn behavior_count(&self) -> usize {
        self.behaviors.len()
    }

    pub fn set_state(
        &mut self,
        state: AgentState,
    ) {
        self.state = state;
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct RuntimeSnapshot {
    pub state: RuntimeState,
    pub agent_count: usize,
    pub running_agents: usize,
    pub behavior_count: usize,
}

#[derive(Debug, Default)]
pub struct CardinalRuntime {
    state: RuntimeState,
    agents: HashMap<AgentId, Agent>,
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

    pub fn start(&mut self) -> Result<(), CoreError> {
        match self.state {
            RuntimeState::Created
            | RuntimeState::Paused => {
                self.state = RuntimeState::Running;
                Ok(())
            }

            RuntimeState::Running => {
                Err(CoreError::InvalidState {
                    message:
                        "runtime is already running"
                            .to_string(),
                })
            }

            RuntimeState::Stopped => {
                Err(CoreError::InvalidState {
                    message:
                        "stopped runtime cannot be started"
                            .to_string(),
                })
            }
        }
    }

    pub fn pause(&mut self) -> Result<(), CoreError> {
        match self.state {
            RuntimeState::Running => {
                self.state = RuntimeState::Paused;

                for agent in self.agents.values_mut() {
                    if agent.state() == AgentState::Running {
                        agent.set_state(
                            AgentState::Paused
                        );
                    }
                }

                Ok(())
            }

            RuntimeState::Paused => {
                Err(CoreError::InvalidState {
                    message:
                        "runtime is already paused"
                            .to_string(),
                })
            }

            _ => Err(CoreError::InvalidState {
                message:
                    "runtime must be running to pause"
                        .to_string(),
            }),
        }
    }

    pub fn stop(&mut self) -> Result<(), CoreError> {
        match self.state {
            RuntimeState::Stopped => {
                Err(CoreError::InvalidState {
                    message:
                        "runtime is already stopped"
                            .to_string(),
                })
            }

            _ => {
                self.state = RuntimeState::Stopped;

                for agent in self.agents.values_mut() {
                    agent.set_state(
                        AgentState::Stopped
                    );
                }

                Ok(())
            }
        }
    }

    pub fn register_agent(
        &mut self,
        agent: Agent,
    ) -> Result<(), CoreError> {
        let id = agent.id().clone();

        if self.agents.contains_key(&id) {
            return Err(
                CoreError::AgentAlreadyExists {
                    agent: id.as_str().to_string(),
                },
            );
        }

        self.agents.insert(id, agent);

        Ok(())
    }

    pub fn get_agent(
        &self,
        id: &AgentId,
    ) -> Result<&Agent, CoreError> {
        self.agents.get(id).ok_or_else(|| {
            CoreError::AgentNotFound {
                agent: id.as_str().to_string(),
            }
        })
    }

    pub fn get_agent_mut(
        &mut self,
        id: &AgentId,
    ) -> Result<&mut Agent, CoreError> {
        self.agents.get_mut(id).ok_or_else(|| {
            CoreError::AgentNotFound {
                agent: id.as_str().to_string(),
            }
        })
    }

    pub fn start_agent(
        &mut self,
        id: &AgentId,
    ) -> Result<(), CoreError> {
        if self.state != RuntimeState::Running {
            return Err(CoreError::InvalidState {
                message:
                    "runtime must be running to start an agent"
                        .to_string(),
            });
        }

        let agent = self.get_agent_mut(id)?;

        match agent.state() {
            AgentState::Created
            | AgentState::Ready
            | AgentState::Paused => {
                agent.set_state(
                    AgentState::Running
                );

                Ok(())
            }

            AgentState::Running => {
                Err(CoreError::InvalidState {
                    message:
                        "agent is already running"
                            .to_string(),
                })
            }

            AgentState::Stopped => {
                Err(CoreError::InvalidState {
                    message:
                        "stopped agent cannot be started"
                            .to_string(),
                })
            }
        }
    }

    pub fn stop_agent(
        &mut self,
        id: &AgentId,
    ) -> Result<(), CoreError> {
        let agent = self.get_agent_mut(id)?;

        if agent.state() == AgentState::Stopped {
            return Err(CoreError::InvalidState {
                message:
                    "agent is already stopped"
                        .to_string(),
            });
        }

        agent.set_state(AgentState::Stopped);

        Ok(())
    }

    pub fn snapshot(&self) -> RuntimeSnapshot {
        let behavior_count = self
            .agents
            .values()
            .map(Agent::behavior_count)
            .sum();

        let running_agents = self
            .agents
            .values()
            .filter(|agent| {
                agent.state() == AgentState::Running
            })
            .count();

        RuntimeSnapshot {
            state: self.state,
            agent_count: self.agents.len(),
            running_agents,
            behavior_count,
        }
    }
}
