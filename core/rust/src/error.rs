use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CoreError {
    EmptyIdentifier {
        kind: &'static str,
    },

    AgentAlreadyExists {
        agent: String,
    },

    AgentNotFound {
        agent: String,
    },

    BehaviorAlreadyExists {
        behavior: String,
    },

    BehaviorNotFound {
        behavior: String,
    },

    InvalidState {
        message: String,
    },
}

impl fmt::Display for CoreError {
    fn fmt(
        &self,
        formatter: &mut fmt::Formatter<'_>,
    ) -> fmt::Result {
        match self {
            Self::EmptyIdentifier { kind } => {
                write!(
                    formatter,
                    "{} identifier cannot be empty",
                    kind
                )
            }

            Self::AgentAlreadyExists { agent } => {
                write!(
                    formatter,
                    "agent already exists: {}",
                    agent
                )
            }

            Self::AgentNotFound { agent } => {
                write!(
                    formatter,
                    "agent not found: {}",
                    agent
                )
            }

            Self::BehaviorAlreadyExists { behavior } => {
                write!(
                    formatter,
                    "behavior already exists: {}",
                    behavior
                )
            }

            Self::BehaviorNotFound { behavior } => {
                write!(
                    formatter,
                    "behavior not found: {}",
                    behavior
                )
            }

            Self::InvalidState { message } => {
                write!(
                    formatter,
                    "invalid core state: {}",
                    message
                )
            }
        }
    }
}

impl std::error::Error for CoreError {}
