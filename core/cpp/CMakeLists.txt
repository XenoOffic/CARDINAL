cmake_minimum_required(VERSION 3.16)

project(
    cardinal_native
    VERSION 0.1.0
    LANGUAGES CXX
)

set(
    CMAKE_CXX_STANDARD
    17
)

set(
    CMAKE_CXX_STANDARD_REQUIRED
    ON
)

set(
    CMAKE_CXX_EXTENSIONS
    OFF
)

add_library(
    cardinal_native
    STATIC
    src/runtime.cpp
)

target_include_directories(
    cardinal_native
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../rust/include
)

add_executable(
    cardinal_native_demo
    examples/native_runtime.cpp
)

target_link_libraries(
    cardinal_native_demo
    PRIVATE
    cardinal_native
)

if(UNIX AND NOT APPLE)
    target_link_libraries(
        cardinal_native_demo
        PRIVATE
        cardinal_core
    )
endif()

if(APPLE)
    target_link_libraries(
        cardinal_native_demo
        PRIVATE
        cardinal_core
    )
endif()

if(WIN32)
    target_link_libraries(
        cardinal_native_demo
        PRIVATE
        cardinal_core
    )
endif()
