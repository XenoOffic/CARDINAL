pub mod error;
pub mod ffi;
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

    fn agent(name: &str) -> Agent {
        Agent::new(
            AgentId::new(name).unwrap()
        )
    }

    fn agent_id(name: &str) -> AgentId {
        AgentId::new(name).unwrap()
    }

    fn behavior_id(name: &str) -> BehaviorId {
        BehaviorId::new(name).unwrap()
    }

    #[test]
    fn runtime_starts() {
        let mut runtime =
            CardinalRuntime::new();

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

        runtime
            .register_agent(agent("agent_a"))
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

        runtime
            .register_agent(agent("agent_a"))
            .unwrap();

        assert!(
            runtime
                .register_agent(agent("agent_a"))
                .is_err()
        );
    }

    #[test]
    fn agent_can_register_behavior() {
        let mut runtime =
            CardinalRuntime::new();

        runtime
            .register_agent(agent("agent_a"))
            .unwrap();

        let id =
            agent_id("agent_a");

        let agent =
            runtime.get_agent_mut(&id).unwrap();

        agent
            .register_behavior(
                behavior_id("tick")
            )
            .unwrap();

        assert!(
            agent.has_behavior(
                &behavior_id("tick")
            )
        );
    }

    #[test]
    fn duplicate_behavior_is_rejected() {
        let mut runtime =
            CardinalRuntime::new();

        runtime
            .register_agent(agent("agent_a"))
            .unwrap();

        let id =
            agent_id("agent_a");

        let agent =
            runtime.get_agent_mut(&id).unwrap();

        agent
            .register_behavior(
                behavior_id("tick")
            )
            .unwrap();

        assert!(
            agent
                .register_behavior(
                    behavior_id("tick")
                )
                .is_err()
        );
    }

    #[test]
    fn running_agent_is_counted() {
        let mut runtime =
            CardinalRuntime::new();

        runtime
            .register_agent(agent("agent_a"))
            .unwrap();

        runtime.start().unwrap();

        let id =
            agent_id("agent_a");

        runtime
            .start_agent(&id)
            .unwrap();

        assert_eq!(
            runtime.snapshot().running_agents,
            1
        );
    }

    #[test]
    fn stopping_agent_removes_it_from_running_count() {
        let mut runtime =
            CardinalRuntime::new();

        runtime
            .register_agent(agent("agent_a"))
            .unwrap();

        runtime.start().unwrap();

        let id =
            agent_id("agent_a");

        runtime
            .start_agent(&id)
            .unwrap();

        runtime
            .stop_agent(&id)
            .unwrap();

        assert_eq!(
            runtime.snapshot().running_agents,
            0
        );
    }

    #[test]
    fn behavior_count_is_reported() {
        let mut runtime =
            CardinalRuntime::new();

        runtime
            .register_agent(agent("agent_a"))
            .unwrap();

        let id =
            agent_id("agent_a");

        let agent =
            runtime.get_agent_mut(&id).unwrap();

        agent
            .register_behavior(
                behavior_id("tick")
            )
            .unwrap();

        agent
            .register_behavior(
                behavior_id("update")
            )
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
            ffi::cardinal_runtime_destroy(
                handle
            );
        }
    }

    #[test]
    fn ffi_start_works() {
        let handle =
            ffi::cardinal_runtime_create();

        assert!(!handle.is_null());

        let result = unsafe {
            ffi::cardinal_runtime_start(
                handle
            )
        };

        assert!(result.success);
        assert_eq!(result.code, 0);
        assert!(
            !result.message.is_null()
        );

        unsafe {
            ffi::cardinal_result_free(
                result.message
            );

            ffi::cardinal_runtime_destroy(
                handle
            );
        }
    }

    #[test]
    fn ffi_register_agent_works() {
        use std::ffi::CString;

        let handle =
            ffi::cardinal_runtime_create();

        assert!(!handle.is_null());

        let name =
            CString::new("agent_a")
                .unwrap();

        let result = unsafe {
            ffi::cardinal_runtime_register_agent(
                handle,
                name.as_ptr(),
            )
        };

        assert!(result.success);

        unsafe {
            ffi::cardinal_result_free(
                result.message
            );

            ffi::cardinal_runtime_destroy(
                handle
            );
        }
    }

    #[test]
    fn ffi_null_handle_is_rejected() {
        let result = unsafe {
            ffi::cardinal_runtime_start(
                std::ptr::null_mut()
            )
        };

        assert!(!result.success);
        assert_eq!(result.code, 1);

        unsafe {
            ffi::cardinal_result_free(
                result.message
            );
        }
    }

    #[test]
    fn ffi_null_agent_name_is_rejected() {
        let handle =
            ffi::cardinal_runtime_create();

        let result = unsafe {
            ffi::cardinal_runtime_register_agent(
                handle,
                std::ptr::null(),
            )
        };

        assert!(!result.success);
        assert_eq!(result.code, 3);

        unsafe {
            ffi::cardinal_result_free(
                result.message
            );

            ffi::cardinal_runtime_destroy(
                handle
            );
        }
    }
}
