#include "cardinal/runtime.hpp"

#include <iostream>
#include <exception>

int main() {
    try {
        cardinal::Runtime runtime;

        runtime.start();

        runtime.register_agent(
            "native_agent"
        );

        runtime.start_agent(
            "native_agent"
        );

        std::cout
            << "CARDINAL native runtime started"
            << std::endl;

        runtime.stop_agent(
            "native_agent"
        );

        runtime.stop();

        std::cout
            << "CARDINAL native runtime stopped"
            << std::endl;

        return 0;
    }
    catch (const std::exception& error) {
        std::cerr
            << "CARDINAL native runtime error: "
            << error.what()
            << std::endl;

        return 1;
    }
}
