# Hegel C Reference

## Table of Contents

- [Setup](#setup) — CMake integration, prerequisites, C99 requirement
- [Test Structure](#test-structure) — `hegel_run_test`, `hegel_settings`, test body callbacks
- [Session Management](#session-management) — `hegel_session_new`, `hegel_session_free`
- [Generator Reference](#generator-reference) — Numeric, boolean, text, binary, collections, format
- [Combinator Methods](#combinator-methods) — `hegel_map`, `hegel_flat_map`, `hegel_filter`, `hegel_one_of`
- [Draw Functions](#draw-functions) — `hegel_draw_int`, `hegel_draw_float`, `hegel_draw_string`, `hegel_draw_bytes`
- [Test Body Helpers](#test-body-helpers) — `hegel_assume`, `hegel_target`, `hegel_note`
- [C-Specific Patterns](#c-specific-patterns) — Memory management, struct generation, error handling

Repository: https://github.com/gburd/hegel-c

## Setup

hegel-c is a C99 static library using CMake 3.14+.

**Prerequisites:**
- C99 compiler (gcc or clang)
- CMake 3.14+
- libcbor
- zlib
- cmocka (for tests)
- The `hegel` binary (from hegel-core)

**CMakeLists.txt integration:**

```cmake
include(FetchContent)
FetchContent_Declare(
    hegel
    GIT_REPOSITORY https://github.com/gburd/hegel-c.git
    GIT_TAG main
)
FetchContent_MakeAvailable(hegel)

target_link_libraries(your_test_target PRIVATE hegel)
```

**Build:**

```bash
mkdir build && cd build
cmake ..
make
make test
```

**Linking:** `-lhegel -lcbor -lz`

**Server binary:** The library spawns the `hegel` server as a subprocess. Set `HEGEL_SERVER_COMMAND` environment variable to override the path.

## Test Structure

hegel-c uses a callback-based test structure. Each test is a function taking `hegel_test_case *tc` and optional user data:

```c
#include <hegel/hegel.h>
#include <hegel/generators.h>

static void my_test(hegel_test_case *tc, void *user_data)
{
    (void)user_data;
    int64_t a = hegel_draw_int(tc, hegel_integers(INT64_MIN, INT64_MAX));
    int64_t b = hegel_draw_int(tc, hegel_integers(INT64_MIN, INT64_MAX));
    assert(a + b == b + a);  /* wrapping semantics in C */
}

int main(void)
{
    hegel_session *s = hegel_session_new();
    hegel_settings settings = HEGEL_DEFAULT_SETTINGS;
    settings.max_examples = 100;

    hegel_results r = hegel_run_test(s, my_test, NULL, &settings);

    hegel_results_free(&r);
    hegel_session_free(s);
    return r.passed ? 0 : 1;
}
```

### Settings

```c
hegel_settings settings = HEGEL_DEFAULT_SETTINGS;
settings.max_examples = 100;    /* number of test cases */
settings.verbosity = 1;         /* 0=quiet, 1=normal, 2=verbose */
```

### Results

```c
hegel_results r = hegel_run_test(s, test_fn, user_data, &settings);
/* r.passed — true if no failing test case found */
/* r.valid_test_cases — number of non-rejected test cases */
/* r.interesting_test_cases — number of failing test cases */
hegel_results_free(&r);
```

## Session Management

```c
hegel_session *s = hegel_session_new();   /* create session, spawns server */
hegel_session_free(s);                     /* tear down session and server */
```

One session can run multiple tests. Create the session once in `main()`.

## Generator Reference

### Numeric Generators

```c
hegel_integers(min, max)        /* int64_t in [min, max] */
hegel_floats(min, max)          /* double in [min, max] */
hegel_booleans()                /* bool */
```

**Full range integers:**

```c
int64_t val = hegel_draw_int(tc, hegel_integers(INT64_MIN, INT64_MAX));
int32_t small = (int32_t)hegel_draw_int(tc, hegel_integers(INT32_MIN, INT32_MAX));
```

### Text and Binary Generators

```c
hegel_text(min_size, max_size)      /* UTF-8 string, caller must free */
hegel_binary(min_size, max_size)    /* byte buffer, caller must free */
```

### Collection Generators

```c
hegel_lists(element_gen, min_size, max_size)
hegel_lists_unique(element_gen, min_size, max_size)
hegel_tuples(gen_array, count)
hegel_dicts(key_gen, val_gen, min_size, max_size)
```

### Constant and Sampling Generators

```c
hegel_just_int(42)
hegel_just_string("hello")
hegel_sampled_from_strings(values, count)
hegel_sampled_from_ints(values, count)
```

### Format Generators

```c
hegel_emails()
hegel_urls()
hegel_domains()
hegel_ip4_addresses()
hegel_ip6_addresses()
hegel_dates()
hegel_times()
hegel_datetimes()
```

## Combinator Methods

```c
hegel_map(source, map_fn, ctx, free_fn)      /* transform drawn values */
hegel_flat_map(source, flatmap_fn, ctx)       /* dependent generation */
hegel_filter(source, predicate_fn, ctx)       /* reject values */
hegel_one_of(gen_array, count)                /* choose from alternatives */
hegel_optional(element_gen)                   /* nullable variant */
```

## Draw Functions

Inside a test body:

```c
int64_t  val  = hegel_draw_int(tc, gen);
double   fval = hegel_draw_float(tc, gen);
bool     bval = hegel_draw_bool(tc, gen);
char    *sval = hegel_draw_string(tc, gen);   /* caller frees */
size_t   len;
uint8_t *data = hegel_draw_bytes(tc, gen, &len);  /* caller frees */
```

## Test Body Helpers

```c
hegel_assume(condition);            /* skip test case if false */
hegel_target(value, "label");       /* guide generation toward a goal */
hegel_note("diagnostic message");   /* attach note, printed on failure */
```

## C-Specific Patterns

### Memory Management

Strings and byte arrays drawn from hegel must be freed by the caller:

```c
static void test_string_roundtrip(hegel_test_case *tc, void *ctx)
{
    char *s = hegel_draw_string(tc, hegel_text(0, 256));
    char *encoded = my_encode(s);
    char *decoded = my_decode(encoded);
    assert(strcmp(s, decoded) == 0);
    free(decoded);
    free(encoded);
    free(s);
}
```

### Struct Generation

Generate struct fields individually:

```c
typedef struct {
    int64_t x;
    int64_t y;
} point_t;

static void test_point_distance(hegel_test_case *tc, void *ctx)
{
    point_t p = {
        .x = hegel_draw_int(tc, hegel_integers(-1000, 1000)),
        .y = hegel_draw_int(tc, hegel_integers(-1000, 1000)),
    };
    double d = point_distance_from_origin(&p);
    assert(d >= 0.0);
}
```

### Integration with cmocka

```c
#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include <hegel/hegel.h>
#include <hegel/generators.h>

static hegel_session *session;

static int setup(void **state)
{
    session = hegel_session_new();
    *state = session;
    return 0;
}

static int teardown(void **state)
{
    hegel_session_free((hegel_session *)*state);
    return 0;
}

static void prop_sort_idempotent(hegel_test_case *tc, void *ctx)
{
    /* ... */
}

static void test_sort_idempotent(void **state)
{
    hegel_session *s = (hegel_session *)*state;
    hegel_settings settings = HEGEL_DEFAULT_SETTINGS;
    hegel_results r = hegel_run_test(s, prop_sort_idempotent, NULL, &settings);
    assert_true(r.passed);
    hegel_results_free(&r);
}

int main(void)
{
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_sort_idempotent),
    };
    return cmocka_run_group_tests(tests, setup, teardown);
}
```

### Error Handling Pattern

Test that error-returning functions never crash on arbitrary input:

```c
static void test_parse_no_crash(hegel_test_case *tc, void *ctx)
{
    char *input = hegel_draw_string(tc, hegel_text(0, 1024));
    int err = 0;
    my_type_t *result = my_parse(input, &err);
    /* Should return NULL with error code, never crash */
    if (result != NULL) {
        my_type_free(result);
    }
    free(input);
}
```
