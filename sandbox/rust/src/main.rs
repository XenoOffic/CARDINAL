use cardinal_sandbox::{
    ResourceLimits,
    Sandbox,
    SandboxRequest,
};

use serde::{Deserialize, Serialize};

use std::io::{
    self,
    BufRead,
    Write,
};

#[derive(Debug, Deserialize)]
struct BridgeRequest {
    experiment_id: String,
    candidate_id: String,
    max_instructions: u64,
    max_memory_bytes: u64,
    max_execution_time_ms: u64,
    instructions_used: u64,
    memory_used_bytes: u64,
    execution_time_ms: u64,
}

#[derive(Debug, Serialize)]
struct BridgeResponse {
    success: bool,
    status: String,
    experiment_id: String,
    candidate_id: String,
    instructions_used: u64,
    memory_used_bytes: u64,
    execution_time_ms: u64,
    message: String,
}

fn status_string(
    status: cardinal_sandbox::SandboxStatus,
) -> String {
    format!("{status:?}").to_lowercase()
}

fn process_request(
    request: BridgeRequest,
) -> BridgeResponse {
    let limits = match ResourceLimits::new(
        request.max_instructions,
        request.max_memory_bytes,
        request.max_execution_time_ms,
    ) {
        Ok(value) => value,

        Err(error) => {
            return BridgeResponse {
                success: false,
                status: "rejected".to_string(),
                experiment_id: request.experiment_id,
                candidate_id: request.candidate_id,
                instructions_used: 0,
                memory_used_bytes: 0,
                execution_time_ms: 0,
                message: error.to_string(),
            };
        }
    };

    let sandbox_request = match SandboxRequest::new(
        request.experiment_id.clone(),
        request.candidate_id.clone(),
        limits,
    ) {
        Ok(value) => value,

        Err(error) => {
            return BridgeResponse {
                success: false,
                status: "rejected".to_string(),
                experiment_id: request.experiment_id,
                candidate_id: request.candidate_id,
                instructions_used: 0,
                memory_used_bytes: 0,
                execution_time_ms: 0,
                message: error.to_string(),
            };
        }
    };

    let mut sandbox = Sandbox::new(
        sandbox_request
    );

    if let Err(error) = sandbox.start() {
        return BridgeResponse {
            success: false,
            status: "rejected".to_string(),
            experiment_id: request.experiment_id,
            candidate_id: request.candidate_id,
            instructions_used: 0,
            memory_used_bytes: 0,
            execution_time_ms: 0,
            message: error.to_string(),
        };
    }

    match sandbox.complete(
        request.instructions_used,
        request.memory_used_bytes,
        request.execution_time_ms,
    ) {
        Ok(result) => {
            BridgeResponse {
                success: result.status
                    == cardinal_sandbox::SandboxStatus::Passed,
                status: status_string(
                    result.status
                ),
                experiment_id: result.experiment_id,
                candidate_id: result.candidate_id,
                instructions_used:
                    result.instructions_used,
                memory_used_bytes:
                    result.memory_used_bytes,
                execution_time_ms:
                    result.execution_time_ms,
                message: result.message,
            }
        }

        Err(error) => {
            BridgeResponse {
                success: false,
                status: "failed".to_string(),
                experiment_id: request.experiment_id,
                candidate_id: request.candidate_id,
                instructions_used:
                    request.instructions_used,
                memory_used_bytes:
                    request.memory_used_bytes,
                execution_time_ms:
                    request.execution_time_ms,
                message: error.to_string(),
            }
        }
    }
}

fn main() {
    let stdin = io::stdin();

    let mut stdout = io::stdout();

    for line in stdin.lock().lines() {
        let line = match line {
            Ok(value) => value,

            Err(error) => {
                let response = BridgeResponse {
                    success: false,
                    status: "failed".to_string(),
                    experiment_id: String::new(),
                    candidate_id: String::new(),
                    instructions_used: 0,
                    memory_used_bytes: 0,
                    execution_time_ms: 0,
                    message: error.to_string(),
                };

                let json = serde_json::to_string(
                    &response
                ).unwrap();

                writeln!(
                    stdout,
                    "{json}"
                ).unwrap();

                continue;
            }
        };

        if line.trim().is_empty() {
            continue;
        }

        let response = match serde_json::from_str::<
            BridgeRequest
        >(&line) {
            Ok(request) => {
                process_request(request)
            }

            Err(error) => BridgeResponse {
                success: false,
                status: "rejected".to_string(),
                experiment_id: String::new(),
                candidate_id: String::new(),
                instructions_used: 0,
                memory_used_bytes: 0,
                execution_time_ms: 0,
                message: format!(
                    "invalid request: {error}"
                ),
            },
        };

        let json = serde_json::to_string(
            &response
        ).unwrap();

        writeln!(
            stdout,
            "{json}"
        ).unwrap();

        stdout.flush().unwrap();
    }
}
