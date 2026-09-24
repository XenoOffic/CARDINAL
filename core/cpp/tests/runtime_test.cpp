#include "cardinal/runtime.hpp"

#include <cassert>
#include <iostream>
#include <utility>

int main()
{
    cardinal::Runtime runtime;

    assert(runtime.valid());

    runtime.start();

    runtime.register_agent(
        "cpp_test_agent"
    );

    runtime.start_agent(
        "cpp_test_agent"
    );

    runtime.stop_agent(
        "cpp_test_agent"
    );

    runtime.stop();

    cardinal::Runtime moved_runtime =
        std::move(runtime);

    assert(moved_runtime.valid());
    assert(!runtime.valid());

    std::cout
        << "CARDINAL C++ integration tests passed"
        << std::endl;

    return 0;
}
