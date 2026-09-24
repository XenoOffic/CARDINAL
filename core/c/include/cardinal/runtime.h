#ifndef CARDINAL_C_RUNTIME_H
#define CARDINAL_C_RUNTIME_H

#include "../../../rust/include/cardinal.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef CardinalRuntimeHandle CardinalCRuntime;

CardinalCRuntime *
cardinal_c_runtime_create(void);

void
cardinal_c_runtime_destroy(
    CardinalCRuntime *runtime
);

CardinalResult
cardinal_c_runtime_start(
    CardinalCRuntime *runtime
);

CardinalResult
cardinal_c_runtime_pause(
    CardinalCRuntime *runtime
);

CardinalResult
cardinal_c_runtime_stop(
    CardinalCRuntime *runtime
);

CardinalResult
cardinal_c_runtime_register_agent(
    CardinalCRuntime *runtime,
    const char *name
);

CardinalResult
cardinal_c_runtime_start_agent(
    CardinalCRuntime *runtime,
    const char *name
);

CardinalResult
cardinal_c_runtime_stop_agent(
    CardinalCRuntime *runtime,
    const char *name
);

void
cardinal_c_result_free(
    char *message
);

#ifdef __cplusplus
}
#endif

#endif
