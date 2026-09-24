cmake_minimum_required(VERSION 3.18)

project(cardinal_c
    VERSION 0.1.0
    LANGUAGES C
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

set(CARDINAL_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}/../.."
)

set(CARDINAL_RUST_DIR
    "${CARDINAL_ROOT}/core/rust"
)

set(CARDINAL_RUST_TARGET_DIR
    "${CARDINAL_RUST_DIR}/target"
)

set(CARDINAL_RUST_LIBRARY
    "${CARDINAL_RUST_TARGET_DIR}/debug/libcardinal_core.a"
)

set(CARDINAL_RUST_INCLUDE_DIR
    "${CARDINAL_RUST_DIR}/include"
)

if(NOT EXISTS "${CARDINAL_RUST_LIBRARY}")
    message(FATAL_ERROR
        "CARDINAL Rust core library not found: ${CARDINAL_RUST_LIBRARY}\n"
        "Build it first with:\n"
        "  cd ${CARDINAL_RUST_DIR}\n"
        "  cargo build"
    )
endif()

add_library(cardinal_c STATIC
    src/runtime.c
)

target_include_directories(cardinal_c
    PUBLIC
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
        "${CARDINAL_RUST_INCLUDE_DIR}"
)

target_link_libraries(cardinal_c
    PUBLIC
        "${CARDINAL_RUST_LIBRARY}"
)

add_executable(cardinal_c_demo
    examples/native_runtime.c
)

target_link_libraries(cardinal_c_demo
    PRIVATE
        cardinal_c
        "${CARDINAL_RUST_LIBRARY}"
)

target_include_directories(cardinal_c_demo
    PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
        "${CARDINAL_RUST_INCLUDE_DIR}"
)

enable_testing()

add_executable(cardinal_c_runtime_test
    tests/runtime_test.c
)

target_link_libraries(cardinal_c_runtime_test
    PRIVATE
        cardinal_c
        "${CARDINAL_RUST_LIBRARY}"
)

target_include_directories(cardinal_c_runtime_test
    PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
        "${CARDINAL_RUST_INCLUDE_DIR}"
)

add_test(
    NAME cardinal_c_runtime_test
    COMMAND cardinal_c_runtime_test
)
