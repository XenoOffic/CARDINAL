//! CARDINAL Sandbox Core
//!
//! This crate defines the safe contract used by CARDINAL experiments.
//!
//! The current implementation does NOT execute arbitrary code.
//! It provides:
//! - sandbox requests
//! - resource limits
//! - execution states
//! - deterministic results
//! - controlled state transitions
//!
//! Future execution backends can implement this contract without
//! changing the higher-level experiment model.

use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SandboxStatus {
    Created,
    Running,
    Passed,
    Failed,
    Rejected,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ResourceLimits {
    pub max_instructions: u64,
    pub max_memory_bytes: u64,
    pub max_execution_time_ms: u64,
}

impl ResourceLimits {
    pub fn new(
        max_instructions: u64,
        max_memory_bytes: u64,
        max_execution_time_ms: u64,
    ) -> Result<Self, SandboxError> {
        if max_instructions == 0 {
            return Err(SandboxError::InvalidLimit(
                "max_instructions must be greater than zero",
            ));
        }

        if max_memory_bytes == 0 {
            return Err(SandboxError::InvalidLimit(
                "max_memory_bytes must be greater than zero",
            ));
        }

        if max_execution_time_ms == 0 {
            return Err(SandboxError::InvalidLimit(
                "max_execution_time_ms must be greater than zero",
            ));
        }

        Ok(Self {
            max_instructions,
            max_memory_bytes,
            max_execution_time_ms,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SandboxRequest {
    pub experiment_id: String,
    pub candidate_id: String,
    pub limits: ResourceLimits,
}

impl SandboxRequest {
    pub fn new(
        experiment_id: impl Into<String>,
        candidate_id: impl Into<String>,
        limits: ResourceLimits,
    ) -> Result<Self, SandboxError> {
        let experiment_id = experiment_id.into();
        let candidate_id = candidate_id.into();

        if experiment_id.is_empty() {
            return Err(SandboxError::EmptyIdentifier(
                "experiment_id",
            ));
        }

        if candidate_id.is_empty() {
            return Err(SandboxError::EmptyIdentifier(
                "candidate_id",
            ));
        }

        Ok(Self {
            experiment_id,
            candidate_id,
            limits,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SandboxResult {
    pub experiment_id: String,
    pub candidate_id: String,
    pub status: SandboxStatus,
    pub instructions_used: u64,
    pub memory_used_bytes: u64,
    pub execution_time_ms: u64,
    pub message: String,
}

impl SandboxResult {
    fn rejected(
        request: &SandboxRequest,
        message: impl Into<String>,
    ) -> Self {
        Self {
            experiment_id: request.experiment_id.clone(),
            candidate_id: request.candidate_id.clone(),
            status: SandboxStatus::Rejected,
            instructions_used: 0,
            memory_used_bytes: 0,
            execution_time_ms: 0,
            message: message.into(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SandboxError {
    InvalidLimit(&'static str),
    EmptyIdentifier(&'static str),
    InvalidState(&'static str),
}

impl fmt::Display for SandboxError {
    fn fmt(
        &self,
        formatter: &mut fmt::Formatter<'_>,
    ) -> fmt::Result {
        match self {
            Self::InvalidLimit(message) => {
                write!(formatter, "invalid resource limit: {message}")
            }

            Self::EmptyIdentifier(name) => {
                write!(formatter, "{name} cannot be empty")
            }

            Self::InvalidState(message) => {
                write!(formatter, "invalid sandbox state: {message}")
            }
        }
    }
}

impl std::error::Error for SandboxError {}

pub struct Sandbox {
    status: SandboxStatus,
    request: SandboxRequest,
}

impl Sandbox {
    pub fn new(
        request: SandboxRequest,
    ) -> Self {
        Self {
            status: SandboxStatus::Created,
            request,
        }
    }

    pub fn status(
        &self,
    ) -> SandboxStatus {
        self.status
    }

    pub fn request(
        &self,
    ) -> &SandboxRequest {
        &self.request
    }

    pub fn start(
        &mut self,
    ) -> Result<(), SandboxError> {
        if self.status != SandboxStatus::Created {
            return Err(
                SandboxError::InvalidState(
                    "only created sandboxes can start",
                ),
            );
        }

        self.status = SandboxStatus::Running;

        Ok(())
    }

    pub fn complete(
        &mut self,
        instructions_used: u64,
        memory_used_bytes: u64,
        execution_time_ms: u64,
    ) -> Result<SandboxResult, SandboxError> {
        if self.status != SandboxStatus::Running {
            return Err(
                SandboxError::InvalidState(
                    "only running sandboxes can complete",
                ),
            );
        }

        let limits = self.request.limits;

        if instructions_used
            > limits.max_instructions
        {
            self.status = SandboxStatus::Failed;

            return Ok(SandboxResult {
                experiment_id: self.request.experiment_id.clone(),
                candidate_id: self.request.candidate_id.clone(),
                status: SandboxStatus::Failed,
                instructions_used,
                memory_used_bytes,
                execution_time_ms,
                message: String::from(
                    "instruction limit exceeded",
                ),
            });
        }

        if memory_used_bytes
            > limits.max_memory_bytes
        {
            self.status = SandboxStatus::Failed;

            return Ok(SandboxResult {
                experiment_id: self.request.experiment_id.clone(),
                candidate_id: self.request.candidate_id.clone(),
                status: SandboxStatus::Failed,
                instructions_used,
                memory_used_bytes,
                execution_time_ms,
                message: String::from(
                    "memory limit exceeded",
                ),
            });
        }

        if execution_time_ms
            > limits.max_execution_time_ms
        {
            self.status = SandboxStatus::Failed;

            return Ok(SandboxResult {
                experiment_id: self.request.experiment_id.clone(),
                candidate_id: self.request.candidate_id.clone(),
                status: SandboxStatus::Failed,
                instructions_used,
                memory_used_bytes,
                execution_time_ms,
                message: String::from(
                    "execution time limit exceeded",
                ),
            });
        }

        self.status = SandboxStatus::Passed;

        Ok(SandboxResult {
            experiment_id: self.request.experiment_id.clone(),
            candidate_id: self.request.candidate_id.clone(),
            status: SandboxStatus::Passed,
            instructions_used,
            memory_used_bytes,
            execution_time_ms,
            message: String::from(
                "sandbox execution completed",
            ),
        })
    }

    pub fn reject(
        &mut self,
        reason: impl Into<String>,
    ) -> Result<SandboxResult, SandboxError> {
        if matches!(
            self.status,
            SandboxStatus::Passed
                | SandboxStatus::Failed
                | SandboxStatus::Rejected
        ) {
            return Err(
                SandboxError::InvalidState(
                    "completed sandboxes cannot be rejected",
                ),
            );
        }

        self.status = SandboxStatus::Rejected;

        Ok(SandboxResult::rejected(
            &self.request,
            reason,
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn limits() -> ResourceLimits {
        ResourceLimits::new(
            1_000,
            1_000_000,
            5_000,
        )
        .unwrap()
    }

    fn request() -> SandboxRequest {
        SandboxRequest::new(
            "exp-001",
            "candidate-001",
            limits(),
        )
        .unwrap()
    }

    #[test]
    fn resource_limits_are_created() {
        let result = ResourceLimits::new(
            100,
            1024,
            1000,
        );

        assert!(result.is_ok());
    }

    #[test]
    fn zero_instruction_limit_is_rejected() {
        let result = ResourceLimits::new(
            0,
            1024,
            1000,
        );

        assert!(matches!(
            result,
            Err(SandboxError::InvalidLimit(_))
        ));
    }

    #[test]
    fn zero_memory_limit_is_rejected() {
        let result = ResourceLimits::new(
            100,
            0,
            1000,
        );

        assert!(matches!(
            result,
            Err(SandboxError::InvalidLimit(_))
        ));
    }

    #[test]
    fn zero_time_limit_is_rejected() {
        let result = ResourceLimits::new(
            100,
            1024,
            0,
        );

        assert!(matches!(
            result,
            Err(SandboxError::InvalidLimit(_))
        ));
    }

    #[test]
    fn empty_experiment_id_is_rejected() {
        let result = SandboxRequest::new(
            "",
            "candidate",
            limits(),
        );

        assert!(matches!(
            result,
            Err(SandboxError::EmptyIdentifier(_))
        ));
    }

    #[test]
    fn empty_candidate_id_is_rejected() {
        let result = SandboxRequest::new(
            "experiment",
            "",
            limits(),
        );

        assert!(matches!(
            result,
            Err(SandboxError::EmptyIdentifier(_))
        ));
    }

    #[test]
    fn sandbox_starts_in_created_state() {
        let sandbox = Sandbox::new(
            request()
        );

        assert_eq!(
            sandbox.status(),
            SandboxStatus::Created
        );
    }

    #[test]
    fn sandbox_can_start() {
        let mut sandbox = Sandbox::new(
            request()
        );

        sandbox.start().unwrap();

        assert_eq!(
            sandbox.status(),
            SandboxStatus::Running
        );
    }

    #[test]
    fn sandbox_successfully_completes() {
        let mut sandbox = Sandbox::new(
            request()
        );

        sandbox.start().unwrap();

        let result = sandbox
            .complete(
                100,
                1024,
                50,
            )
            .unwrap();

        assert_eq!(
            result.status,
            SandboxStatus::Passed
        );

        assert_eq!(
            sandbox.status(),
            SandboxStatus::Passed
        );
    }

    #[test]
    fn instruction_limit_causes_failure() {
        let mut sandbox = Sandbox::new(
            request()
        );

        sandbox.start().unwrap();

        let result = sandbox
            .complete(
                1_001,
                1024,
                50,
            )
            .unwrap();

        assert_eq!(
            result.status,
            SandboxStatus::Failed
        );

        assert_eq!(
            sandbox.status(),
            SandboxStatus::Failed
        );
    }

    #[test]
    fn memory_limit_causes_failure() {
        let mut sandbox = Sandbox::new(
            request()
        );

        sandbox.start().unwrap();

        let result = sandbox
            .complete(
                100,
                1_000_001,
                50,
            )
            .unwrap();

        assert_eq!(
            result.status,
            SandboxStatus::Failed
        );
    }

    #[test]
    fn execution_time_limit_causes_failure() {
        let mut sandbox = Sandbox::new(
            request()
        );

        sandbox.start().unwrap();

        let result = sandbox
            .complete(
                100,
                1024,
                5_001,
            )
            .unwrap();

        assert_eq!(
            result.status,
            SandboxStatus::Failed
        );
    }

    #[test]
    fn sandbox_can_be_rejected() {
        let mut sandbox = Sandbox::new(
            request()
        );

        let result = sandbox
            .reject("policy denied")
            .unwrap();

        assert_eq!(
            result.status,
            SandboxStatus::Rejected
        );

        assert_eq!(
            sandbox.status(),
            SandboxStatus::Rejected
        );
    }

    #[test]
    fn sandbox_cannot_start_twice() {
        let mut sandbox = Sandbox::new(
            request()
        );

        sandbox.start().unwrap();

        let result = sandbox.start();

        assert!(matches!(
            result,
            Err(SandboxError::InvalidState(_))
        ));
    }

    #[test]
    fn sandbox_cannot_complete_before_start() {
        let mut sandbox = Sandbox::new(
            request()
        );

        let result = sandbox.complete(
            1,
            1,
            1,
        );

        assert!(matches!(
            result,
            Err(SandboxError::InvalidState(_))
        ));
    }

    #[test]
    fn sandbox_cannot_reject_after_completion() {
        let mut sandbox = Sandbox::new(
            request()
        );

        sandbox.start().unwrap();

        sandbox
            .complete(
                1,
                1,
                1,
            )
            .unwrap();

        let result = sandbox.reject(
            "too late",
        );

        assert!(matches!(
            result,
            Err(SandboxError::InvalidState(_))
        ));
    }
}
