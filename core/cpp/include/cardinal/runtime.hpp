#ifndef CARDINAL_RUNTIME_HPP
#define CARDINAL_RUNTIME_HPP

#include <string>

extern "C" {
#include "../../rust/include/cardinal.h"
}

namespace cardinal {

class Runtime {
public:
    Runtime();

    ~Runtime();

    Runtime(const Runtime&) = delete;
    Runtime& operator=(const Runtime&) = delete;

    Runtime(Runtime&& other) noexcept;

    Runtime& operator=(Runtime&& other) noexcept;

    void start();

    void pause();

    void stop();

    void register_agent(
        const std::string& name
    );

    void start_agent(
        const std::string& name
    );

    void stop_agent(
        const std::string& name
    );

    bool valid() const noexcept;

private:
    CardinalRuntimeHandle* handle_;

    void check_result(
        CardinalResult result
    );
};

} // namespace cardinal

#endif
