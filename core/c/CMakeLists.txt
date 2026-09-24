cmake_minimum_required(VERSION 3.16)

project(
    cardinal_c
    VERSION 0.1.0
    LANGUAGES C
)

set(
    CMAKE_C_STANDARD
    11
)

set(
    CMAKE_C_STANDARD_REQUIRED
    ON
)

set(
    CMAKE_C_EXTENSIONS
    OFF
)

add_library(
    cardinal_c
    STATIC
    src/runtime.c
)

target_include_directories(
    cardinal_c
    PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/../rust/include
)

add_executable(
    cardinal_c_demo
    examples/native_runtime.c
)

target_link_libraries(
    cardinal_c_demo
    PRIVATE
    cardinal_c
)

if(UNIX AND NOT APPLE)
    target_link_libraries(
        cardinal_c_demo
        PRIVATE
        cardinal_core
    )
endif()

if(APPLE)
    target_link_libraries(
        cardinal_c_demo
        PRIVATE
        cardinal_core
    )
endif()

if(WIN32)
    target_link_libraries(
        cardinal_c_demo
        PRIVATE
        cardinal_core
    )
endif()
