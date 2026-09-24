#include "cardinal/runtime.h"

CardinalCRuntime *
cardinal_c_runtime_create(void)
{
    return cardinal_runtime_create();
}

void
cardinal_c_runtime_destroy(
    CardinalCRuntime *runtime
)
{
    cardinal_runtime_destroy(runtime);
}

CardinalResult
cardinal_c_runtime_start(
    CardinalCRuntime *runtime
)
{
    return cardinal_runtime_start(runtime);
}

CardinalResult
cardinal_c_runtime_pause(
    CardinalCRuntime *runtime
)
{
    return cardinal_runtime_pause(runtime);
}

CardinalResult
cardinal_c_runtime_stop(
    CardinalCRuntime *runtime
)
{
    return cardinal_runtime_stop(runtime);
}

CardinalResult
cardinal_c_runtime_register_agent(
    CardinalCRuntime *runtime,
    const char *name
)
{
    return cardinal_runtime_register_agent(
        runtime,
        name
    );
}

CardinalResult
cardinal_c_runtime_start_agent(
    CardinalCRuntime *runtime,
    const char *name
)
{
    return cardinal_runtime_start_agent(
        runtime,
        name
    );
}

CardinalResult
cardinal_c_runtime_stop_agent(
    CardinalCRuntime *runtime,
    const char *name
)
{
    return cardinal_runtime_stop_agent(
        runtime,
        name
    );
}

void
cardinal_c_result_free(
    char *message
)
{
    cardinal_result_free(message);
}
