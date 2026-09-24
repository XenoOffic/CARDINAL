pub mod error;
pub mod ids;
pub mod runtime;

pub use error::CoreError;

pub use ids::{
    AgentId,
    BehaviorId,
    ExperimentId,
};

pub use runtime::{
    Agent,
    AgentState,
    CardinalRuntime,
    RuntimeSnapshot,
    RuntimeState,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runtime_starts_in_created_state() {
        let runtime = CardinalRuntime::new();

        assert_eq!(
            runtime.state(),
            RuntimeState::Created
        );
    }

    #[test]
    fn runtime_can_start() {
        let mut runtime =
            CardinalRuntime::new();

        runtime.start().unwrap();

        assert_eq!(
            runtime.state(),
            RuntimeState::Running
        );
    }

    #[test]
    fn runtime_can_pause() {
        let mut runtime =
            CardinalRuntime::new();

        runtime.start().unwrap();
        runtime.pause().unwrap();

        assert_eq!(
            runtime.state(),
            RuntimeState::Paused
        );
    }

    #[test]
    fn runtime_can_stop() {
        let mut runtime =
            CardinalRuntime::new();

        runtime.start().unwrap();
        runtime.stop().unwrap();

        assert_eq!(
            runtime.state(),
            RuntimeState::Stopped
        );
    }

    #[test]
    fn agent_can_be_registered() {
        let mut runtime =
            CardinalRuntime::new();

        let agent_id =
            AgentId::new("alpha").unwrap();

        runtime
            .register_agent(
                Agent::new(
                    agent_id.clone()
                )
            )
            .unwrap();

        assert_eq!(
            runtime.snapshot().agent_count,
            1
        );
    }

    #[test]
    fn duplicate_agent_is_rejected() {
        let mut runtime =
            CardinalRuntime::new();

        let agent_id =
            AgentId::new("alpha").unwrap();

        runtime
            .register_agent(
                Agent::new(
                    agent_id.clone()
                )
            )
            .unwrap();

        let result =
            runtime.register_agent(
                Agent::new(agent_id)
            );

        assert!(matches!(
            result,
            Err(
                CoreError::AgentAlreadyExists { .. }
            )
        ));
    }

    #[test]
    fn agent_can_register_behavior() {
        let mut agent =
            Agent::new(
                AgentId::new("alpha")
                    .unwrap()
            );

        agent
            .register_behavior(
                BehaviorId::new("think")
                    .unwrap()
            )
            .unwrap();

        assert_eq!(
            agent.behavior_count(),
            1
        );
    }

    #[test]
    fn duplicate_behavior_is_rejected() {
        let mut agent =
            Agent::new(
                AgentId::new("alpha")
                    .unwrap()
            );

        let behavior =
            BehaviorId::new("think")
                .unwrap();

        agent
            .register_behavior(
                behavior.clone()
            )
            .unwrap();

        let result =
            agent.register_behavior(
                behavior
            );

        assert!(matches!(
            result,
            Err(
                CoreError::BehaviorAlreadyExists { .. }
            )
        ));
    }

    #[test]
    fn running_agent_is_visible_in_snapshot() {
        let mut runtime =
            CardinalRuntime::new();

        let agent_id =
            AgentId::new("alpha").unwrap();

        runtime
            .register_agent(
                Agent::new(
                    agent_id.clone()
                )
            )
            .unwrap();

        runtime.start().unwrap();
        runtime
            .start_agent(&agent_id)
            .unwrap();

        let snapshot =
            runtime.snapshot();

        assert_eq!(
            snapshot.running_agents,
            1
        );
    }

    #[test]
    fn stopped_runtime_stops_agents() {
        let mut runtime =
            CardinalRuntime::new();

        let agent_id =
            AgentId::new("alpha").unwrap();

        runtime
            .register_agent(
                Agent::new(
                    agent_id.clone()
                )
            )
            .unwrap();

        runtime.start().unwrap();

        runtime
            .start_agent(&agent_id)
            .unwrap();

        runtime.stop().unwrap();

        assert_eq!(
            runtime
                .get_agent(&agent_id)
                .unwrap()
                .state,
            AgentState::Stopped
        );
    }

    #[test]
    fn snapshot_counts_behaviors() {
        let mut runtime =
            CardinalRuntime::new();

        let mut agent =
            Agent::new(
                AgentId::new("alpha")
                    .unwrap()
            );

        agent
            .register_behavior(
                BehaviorId::new("think")
                    .unwrap()
            )
            .unwrap();

        agent
            .register_behavior(
                BehaviorId::new("act")
                    .unwrap()
            )
            .unwrap();

        runtime
            .register_agent(agent)
            .unwrap();

        assert_eq!(
            runtime
                .snapshot()
                .behavior_count,
            2
        );
    }
}
