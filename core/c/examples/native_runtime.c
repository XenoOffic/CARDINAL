#include "cardinal/runtime.h"

#include <stdio.h>

static int
check_result(
    CardinalResult result
)
{
    if (!result.success) {
        if (result.message != NULL) {
            fprintf(
                stderr,
                "CARDINAL error: %s\n",
                result.message
            );

            cardinal_c_result_free(
                result.message
            );
        }

        return 0;
    }

    if (result.message != NULL) {
        cardinal_c_result_free(
            result.message
        );
    }

    return 1;
}

int
main(void)
{
    CardinalCRuntime *runtime =
        cardinal_c_runtime_create();

    if (runtime == NULL) {
        fprintf(
            stderr,
            "Failed to create CARDINAL runtime\n"
        );

        return 1;
    }

    if (!check_result(
        cardinal_c_runtime_start(runtime)
    )) {
        cardinal_c_runtime_destroy(runtime);
        return 1;
    }

    if (!check_result(
        cardinal_c_runtime_register_agent(
            runtime,
            "native_c_agent"
        )
    )) {
        cardinal_c_runtime_destroy(runtime);
        return 1;
    }

    if (!check_result(
        cardinal_c_runtime_start_agent(
            runtime,
            "native_c_agent"
        )
    )) {
        cardinal_c_runtime_destroy(runtime);
        return 1;
    }

    printf(
        "CARDINAL C runtime started\n"
    );

    if (!check_result(
        cardinal_c_runtime_stop_agent(
            runtime,
            "native_c_agent"
        )
    )) {
        cardinal_c_runtime_destroy(runtime);
        return 1;
    }

    if (!check_result(
        cardinal_c_runtime_stop(runtime)
    )) {
        cardinal_c_runtime_destroy(runtime);
        return 1;
    }

    printf(
        "CARDINAL C runtime stopped\n"
    );

    cardinal_c_runtime_destroy(runtime);

    return 0;
}
