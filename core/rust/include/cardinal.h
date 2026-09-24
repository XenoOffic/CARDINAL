#ifndef CARDINAL_H
#define CARDINAL_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stdint.h>

typedef struct CardinalRuntimeHandle
    CardinalRuntimeHandle;

typedef struct CardinalResult {
    bool success;
    int32_t code;
    char *message;
} CardinalResult;

/*
 * Runtime lifecycle
 */

CardinalRuntimeHandle *
cardinal_runtime_create(void);

void
cardinal_runtime_destroy(
    CardinalRuntimeHandle *handle
);

CardinalResult
cardinal_runtime_start(
    CardinalRuntimeHandle *handle
);

CardinalResult
cardinal_runtime_pause(
    CardinalRuntimeHandle *handle
);

CardinalResult
cardinal_runtime_stop(
    CardinalRuntimeHandle *handle
);

/*
 * Agent lifecycle
 */

CardinalResult
cardinal_runtime_register_agent(
    CardinalRuntimeHandle *handle,
    const char *name
);

CardinalResult
cardinal_runtime_start_agent(
    CardinalRuntimeHandle *handle,
    const char *name
);

CardinalResult
cardinal_runtime_stop_agent(
    CardinalRuntimeHandle *handle,
    const char *name
);

/*
 * Memory management
 *
 * Any message returned inside CardinalResult
 * must be released with cardinal_result_free().
 */

void
cardinal_result_free(
    char *message
);

/*
 * Utility
 */

CardinalResult
cardinal_null_result(void);

#ifdef __cplusplus
}
#endif

#endif /* CARDINAL_H */
