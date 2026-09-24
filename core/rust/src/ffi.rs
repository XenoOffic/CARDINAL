use std::ffi::{c_char, CStr, CString};
use std::ptr;

use crate::runtime::CardinalRuntime;

#[repr(C)]
pub struct CardinalRuntimeHandle {
    runtime: CardinalRuntime,
}

#[repr(C)]
pub struct CardinalResult {
    pub success: bool,
    pub code: i32,
    pub message: *mut c_char,
}

impl CardinalResult {
    fn success(message: &str) -> Self {
        Self {
            success: true,
            code: 0,
            message: CString::new(message)
                .unwrap_or_else(|_| {
                    CString::new("success").unwrap()
                })
                .into_raw(),
        }
    }

    fn error(code: i32, message: &str) -> Self {
        Self {
            success: false,
            code,
            message: CString::new(message)
                .unwrap_or_else(|_| {
                    CString::new("error").unwrap()
                })
                .into_raw(),
        }
    }
}

fn read_c_string(
    value: *const c_char,
) -> Result<&'static str, CardinalResult> {
    if value.is_null() {
        return Err(CardinalResult::error(
            3,
            "string pointer is null",
        ));
    }

    let c_string = unsafe {
        CStr::from_ptr(value)
    };

    match c_string.to_str() {
        Ok(value) => {
            /*
             * The returned reference is only used during
             * the current FFI call.
             *
             * The lifetime is intentionally hidden behind
             * this helper because the C string is owned by
             * the caller.
             */
            Ok(unsafe {
                std::mem::transmute::<
                    &str,
                    &'static str,
                >(value)
            })
        }
        Err(_) => Err(
            CardinalResult::error(
                4,
                "string is not valid UTF-8",
            )
        ),
    }
}

#[no_mangle]
pub extern "C" fn cardinal_runtime_create(
) -> *mut CardinalRuntimeHandle {
    let handle = CardinalRuntimeHandle {
        runtime: CardinalRuntime::new(),
    };

    Box::into_raw(Box::new(handle))
}

#[no_mangle]
pub unsafe extern "C" fn cardinal_runtime_destroy(
    handle: *mut CardinalRuntimeHandle,
) {
    if handle.is_null() {
        return;
    }

    drop(Box::from_raw(handle));
}

#[no_mangle]
pub unsafe extern "C" fn cardinal_runtime_start(
    handle: *mut CardinalRuntimeHandle,
) -> CardinalResult {
    if handle.is_null() {
        return CardinalResult::error(
            1,
            "runtime handle is null",
        );
    }

    let runtime = &mut (*handle).runtime;

    match runtime.start() {
        Ok(()) => {
            CardinalResult::success(
                "runtime started",
            )
        }

        Err(error) => {
            CardinalResult::error(
                2,
                &error.to_string(),
            )
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cardinal_runtime_pause(
    handle: *mut CardinalRuntimeHandle,
) -> CardinalResult {
    if handle.is_null() {
        return CardinalResult::error(
            1,
            "runtime handle is null",
        );
    }

    let runtime = &mut (*handle).runtime;

    match runtime.pause() {
        Ok(()) => {
            CardinalResult::success(
                "runtime paused",
            )
        }

        Err(error) => {
            CardinalResult::error(
                2,
                &error.to_string(),
            )
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cardinal_runtime_stop(
    handle: *mut CardinalRuntimeHandle,
) -> CardinalResult {
    if handle.is_null() {
        return CardinalResult::error(
            1,
            "runtime handle is null",
        );
    }

    let runtime = &mut (*handle).runtime;

    match runtime.stop() {
        Ok(()) => {
            CardinalResult::success(
                "runtime stopped",
            )
        }

        Err(error) => {
            CardinalResult::error(
                2,
                &error.to_string(),
            )
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cardinal_runtime_register_agent(
    handle: *mut CardinalRuntimeHandle,
    name: *const c_char,
) -> CardinalResult {
    if handle.is_null() {
        return CardinalResult::error(
            1,
            "runtime handle is null",
        );
    }

    let name = match read_c_string(name) {
        Ok(value) => value,
        Err(result) => return result,
    };

    if name.is_empty() {
        return CardinalResult::error(
            5,
            "agent name is empty",
        );
    }

    let runtime = &mut (*handle).runtime;

    match runtime.register_agent(name) {
        Ok(()) => {
            CardinalResult::success(
                "agent registered",
            )
        }

        Err(error) => {
            CardinalResult::error(
                6,
                &error.to_string(),
            )
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cardinal_runtime_start_agent(
    handle: *mut CardinalRuntimeHandle,
    name: *const c_char,
) -> CardinalResult {
    if handle.is_null() {
        return CardinalResult::error(
            1,
            "runtime handle is null",
        );
    }

    let name = match read_c_string(name) {
        Ok(value) => value,
        Err(result) => return result,
    };

    if name.is_empty() {
        return CardinalResult::error(
            5,
            "agent name is empty",
        );
    }

    let runtime = &mut (*handle).runtime;

    match runtime.start_agent(name) {
        Ok(()) => {
            CardinalResult::success(
                "agent started",
            )
        }

        Err(error) => {
            CardinalResult::error(
                6,
                &error.to_string(),
            )
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cardinal_runtime_stop_agent(
    handle: *mut CardinalRuntimeHandle,
    name: *const c_char,
) -> CardinalResult {
    if handle.is_null() {
        return CardinalResult::error(
            1,
            "runtime handle is null",
        );
    }

    let name = match read_c_string(name) {
        Ok(value) => value,
        Err(result) => return result,
    };

    if name.is_empty() {
        return CardinalResult::error(
            5,
            "agent name is empty",
        );
    }

    let runtime = &mut (*handle).runtime;

    match runtime.stop_agent(name) {
        Ok(()) => {
            CardinalResult::success(
                "agent stopped",
            )
        }

        Err(error) => {
            CardinalResult::error(
                6,
                &error.to_string(),
            )
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn cardinal_result_free(
    message: *mut c_char,
) {
    if message.is_null() {
        return;
    }

    drop(CString::from_raw(message));
}

#[no_mangle]
pub extern "C" fn cardinal_null_result(
) -> CardinalResult {
    CardinalResult {
        success: false,
        code: 1,
        message: ptr::null_mut(),
    }
}
