pub mod error;
pub mod ffi;
pub mod ids;
pub mod runtime;

pub use error::CoreError;
pub use ids::{AgentId, BehaviorId, ExperimentId};
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
    fn runtime_starts() {
        let mut runtime = CardinalRuntime::new();

        assert_eq!(
            runtime.state(),
            RuntimeState::Created
        );

        runtime.start().unwrap();

        assert_eq!(
            runtime.state(),
            RuntimeState::Running
        );
    }

    #[test]
    fn runtime_can_pause() {
        let mut runtime = CardinalRuntime::new();

        runtime.start().unwrap();
        runtime.pause().unwrap();

        assert_eq!(
            runtime.state(),
            RuntimeState::Paused
        );
    }

    #[test]
    fn runtime_can_stop() {
        let mut runtime = CardinalRuntime::new();

        runtime.start().unwrap();
        runtime.stop().unwrap();

        assert_eq!(
            runtime.state(),
            RuntimeState::Stopped
        );
    }

    #[test]
    fn agent_can_be_registered() {
        let mut runtime = CardinalRuntime::new();

        runtime
            .register_agent("agent_a")
            .unwrap();

        assert_eq!(
            runtime.snapshot().agent_count,
            1
        );
    }

    #[test]
    fn duplicate_agent_is_rejected() {
        let mut runtime = CardinalRuntime::new();

        runtime
            .register_agent("agent_a")
            .unwrap();

        assert!(
            runtime
                .register_agent("agent_a")
                .is_err()
        );
    }

    #[test]
    fn agent_can_register_behavior() {
        let mut runtime = CardinalRuntime::new();

        runtime
            .register_agent("agent_a")
            .unwrap();

        let agent = runtime
            .get_agent_mut("agent_a")
            .unwrap();

        agent
            .register_behavior("tick")
            .unwrap();

        assert!(
            agent.has_behavior("tick")
        );
    }

    #[test]
    fn duplicate_behavior_is_rejected() {
        let mut runtime = CardinalRuntime::new();

        runtime
            .register_agent("agent_a")
            .unwrap();

        let agent = runtime
            .get_agent_mut("agent_a")
            .unwrap();

        agent
            .register_behavior("tick")
            .unwrap();

        assert!(
            agent
                .register_behavior("tick")
                .is_err()
        );
    }

    #[test]
    fn running_agent_is_counted() {
        let mut runtime = CardinalRuntime::new();

        runtime
            .register_agent("agent_a")
            .unwrap();

        runtime.start().unwrap();
        runtime
            .start_agent("agent_a")
            .unwrap();

        let snapshot = runtime.snapshot();

        assert_eq!(
            snapshot.running_agents,
            1
        );
    }

    #[test]
    fn stopping_agent_removes_it_from_running_count() {
        let mut runtime = CardinalRuntime::new();

        runtime
            .register_agent("agent_a")
            .unwrap();

        runtime.start().unwrap();
        runtime
            .start_agent("agent_a")
            .unwrap();

        runtime
            .stop_agent("agent_a")
            .unwrap();

        assert_eq!(
            runtime.snapshot().running_agents,
            0
        );
    }

    #[test]
    fn behavior_count_is_reported() {
        let mut runtime = CardinalRuntime::new();

        runtime
            .register_agent("agent_a")
            .unwrap();

        let agent = runtime
            .get_agent_mut("agent_a")
            .unwrap();

        agent
            .register_behavior("tick")
            .unwrap();

        agent
            .register_behavior("update")
            .unwrap();

        assert_eq!(
            runtime.snapshot().behavior_count,
            2
        );
    }

    #[test]
    fn ffi_runtime_handle_can_be_created_and_destroyed() {
        let handle =
            ffi::cardinal_runtime_create();

        assert!(!handle.is_null());

        unsafe {
            ffi::cardinal_runtime_destroy(handle);
        }
    }
}
