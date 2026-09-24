use std::collections::{HashMap, HashSet};

use serde::{Deserialize, Serialize};

use crate::error::CoreError;
use crate::ids::{
    AgentId,
    BehaviorId,
};

#[derive(
    Debug,
    Clone,
    Copy,
    PartialEq,
    Eq,
    Serialize,
    Deserialize,
)]
pub enum RuntimeState {
    Created,
    Running,
    Paused,
    Stopped,
}

#[derive(
    Debug,
    Clone,
    Copy,
    PartialEq,
    Eq,
    Serialize,
    Deserialize,
)]
pub enum AgentState {
    Created,
    Ready,
    Running,
    Paused,
    Stopped,
}

#[derive(
    Debug,
    Clone,
    PartialEq,
    Eq,
    Serialize,
    Deserialize,
)]
pub struct Agent {
    pub id: AgentId,
    pub state: AgentState,
    behaviors: HashSet<BehaviorId>,
}

impl Agent {
    pub fn new(
        id: AgentId,
    ) -> Self {
        Self {
            id,
            state: AgentState::Created,
            behaviors: HashSet::new(),
        }
    }

    pub fn register_behavior(
        &mut self,
        behavior: BehaviorId,
    ) -> Result<(), CoreError> {
        if !self.behaviors.insert(behavior.clone()) {
            return Err(
                CoreError::BehaviorAlreadyExists {
                    behavior: behavior
                        .as_str()
                        .to_string(),
                }
            );
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

#[derive(
    Debug,
    Clone,
    PartialEq,
    Eq,
    Serialize,
    Deserialize,
)]
pub struct RuntimeSnapshot {
    pub state: RuntimeState,
    pub agent_count: usize,
    pub running_agents: usize,
    pub behavior_count: usize,
}

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
            | RuntimeState::Stopped
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
        }
    }

    pub fn pause(&mut self) -> Result<(), CoreError> {
        if self.state != RuntimeState::Running {
            return Err(
                CoreError::InvalidState {
                    message:
                        "only a running runtime can be paused"
                            .to_string(),
                }
            );
        }

        self.state = RuntimeState::Paused;

        Ok(())
    }

    pub fn stop(&mut self) -> Result<(), CoreError> {
        if self.state == RuntimeState::Created {
            return Err(
                CoreError::InvalidState {
                    message:
                        "cannot stop a runtime that has not started"
                            .to_string(),
                }
            );
        }

        self.state = RuntimeState::Stopped;

        for agent in self.agents.values_mut() {
            agent.set_state(
                AgentState::Stopped
            );
        }

        Ok(())
    }

    pub fn register_agent(
        &mut self,
        agent: Agent,
    ) -> Result<(), CoreError> {
        let id = agent.id.clone();

        if self.agents.contains_key(&id) {
            return Err(
                CoreError::AgentAlreadyExists {
                    agent: id.as_str().to_string(),
                }
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
            return Err(
                CoreError::InvalidState {
                    message:
                        "runtime must be running before starting an agent"
                            .to_string(),
                }
            );
        }

        let agent = self.get_agent_mut(id)?;

        agent.set_state(
            AgentState::Running
        );

        Ok(())
    }

    pub fn stop_agent(
        &mut self,
        id: &AgentId,
    ) -> Result<(), CoreError> {
        let agent = self.get_agent_mut(id)?;

        agent.set_state(
            AgentState::Stopped
        );

        Ok(())
    }

    pub fn snapshot(
        &self,
    ) -> RuntimeSnapshot {
        let running_agents = self
            .agents
            .values()
            .filter(|agent| {
                agent.state
                    == AgentState::Running
            })
            .count();

        let behavior_count = self
            .agents
            .values()
            .map(Agent::behavior_count)
            .sum();

        RuntimeSnapshot {
            state: self.state,
            agent_count: self.agents.len(),
            running_agents,
            behavior_count,
        }
    }
}

impl Default for CardinalRuntime {
    fn default() -> Self {
        Self::new()
    }
}
