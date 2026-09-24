#include "cardinal/runtime.h"

#include <assert.h>
#include <stdio.h>

int main(void)
{
    CardinalCRuntime *runtime =
        cardinal_c_runtime_create();

    assert(runtime != NULL);

    CardinalResult result =
        cardinal_c_runtime_start(runtime);

    assert(result.success);
    cardinal_c_result_free(result.message);

    result =
        cardinal_c_runtime_register_agent(
            runtime,
            "test_agent"
        );

    assert(result.success);
    cardinal_c_result_free(result.message);

    result =
        cardinal_c_runtime_start_agent(
            runtime,
            "test_agent"
        );

    assert(result.success);
    cardinal_c_result_free(result.message);

    result =
        cardinal_c_runtime_stop_agent(
            runtime,
            "test_agent"
        );

    assert(result.success);
    cardinal_c_result_free(result.message);

    result =
        cardinal_c_runtime_stop(runtime);

    assert(result.success);
    cardinal_c_result_free(result.message);

    cardinal_c_runtime_destroy(runtime);

    printf(
        "CARDINAL C integration tests passed\n"
    );

    return 0;
}
