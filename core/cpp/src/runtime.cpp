#include "cardinal/runtime.hpp"

#include <stdexcept>
#include <utility>

namespace cardinal {

Runtime::Runtime()
    : handle_(cardinal_runtime_create()) {
    if (handle_ == nullptr) {
        throw std::runtime_error(
            "failed to create CARDINAL runtime"
        );
    }
}

Runtime::~Runtime() {
    if (handle_ != nullptr) {
        cardinal_runtime_destroy(handle_);
        handle_ = nullptr;
    }
}

Runtime::Runtime(
    Runtime&& other
) noexcept
    : handle_(other.handle_) {
    other.handle_ = nullptr;
}

Runtime& Runtime::operator=(
    Runtime&& other
) noexcept {
    if (this == &other) {
        return *this;
    }

    if (handle_ != nullptr) {
        cardinal_runtime_destroy(handle_);
    }

    handle_ = other.handle_;
    other.handle_ = nullptr;

    return *this;
}

void Runtime::check_result(
    CardinalResult result
) {
    std::string message;

    if (result.message != nullptr) {
        message = result.message;

        cardinal_result_free(
            result.message
        );
    }

    if (!result.success) {
        if (message.empty()) {
            message = "CARDINAL runtime operation failed";
        }

        throw std::runtime_error(message);
    }
}

void Runtime::start() {
    check_result(
        cardinal_runtime_start(handle_)
    );
}

void Runtime::pause() {
    check_result(
        cardinal_runtime_pause(handle_)
    );
}

void Runtime::stop() {
    check_result(
        cardinal_runtime_stop(handle_)
    );
}

void Runtime::register_agent(
    const std::string& name
) {
    check_result(
        cardinal_runtime_register_agent(
            handle_,
            name.c_str()
        )
    );
}

void Runtime::start_agent(
    const std::string& name
) {
    check_result(
        cardinal_runtime_start_agent(
            handle_,
            name.c_str()
        )
    );
}

void Runtime::stop_agent(
    const std::string& name
) {
    check_result(
        cardinal_runtime_stop_agent(
            handle_,
            name.c_str()
        )
    );
}

bool Runtime::valid() const noexcept {
    return handle_ != nullptr;
}

} // namespace cardinal
