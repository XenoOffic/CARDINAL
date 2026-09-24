cmake_minimum_required(VERSION 3.18)

project(cardinal_cpp
    VERSION 0.1.0
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

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

add_library(cardinal_native STATIC
    src/runtime.cpp
)

target_include_directories(cardinal_native
    PUBLIC
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
        "${CARDINAL_RUST_INCLUDE_DIR}"
)

target_link_libraries(cardinal_native
    PUBLIC
        "${CARDINAL_RUST_LIBRARY}"
)

add_executable(cardinal_native_demo
    examples/native_runtime.cpp
)

target_include_directories(cardinal_native_demo
    PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
        "${CARDINAL_RUST_INCLUDE_DIR}"
)

target_link_libraries(cardinal_native_demo
    PRIVATE
        cardinal_native
        "${CARDINAL_RUST_LIBRARY}"
)

enable_testing()

add_executable(cardinal_cpp_runtime_test
    tests/runtime_test.cpp
)

target_include_directories(cardinal_cpp_runtime_test
    PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/include"
        "${CARDINAL_RUST_INCLUDE_DIR}"
)

target_link_libraries(cardinal_cpp_runtime_test
    PRIVATE
        cardinal_native
        "${CARDINAL_RUST_LIBRARY}"
)

add_test(
    NAME cardinal_cpp_runtime_test
    COMMAND cardinal_cpp_runtime_test
)
