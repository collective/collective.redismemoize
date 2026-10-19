(reference-configuration)=

# Configuration

<!-- source: src/collective/redismemoize/config.py (DEFAULTS, from_environ) -->

The package reads its configuration from environment variables, once per process, when a cached function is first called.
It has no control panel and no registry records.
Changing a variable requires restarting the instance.

An unset or empty variable takes its default.
An invalid value raises `ValueError`, naming the variable, and the instance does not start.

## Environment variables

| Variable | Default | Accepts |
| --- | --- | --- |
| `REDIS_MEMOIZE_URL` | unset | A URL with the scheme `redis`, `rediss`, or `unix`. Unset, the package is inert. |
| `REDIS_MEMOIZE_PREFIX` | `plone.memoize` | Text without spaces. Every key starts with it. |
| `REDIS_MEMOIZE_TTL` | `86400` | An integer of at least 1, in seconds. The lifetime of a value in Redis. |
| `REDIS_MEMOIZE_TIMEOUT` | `0.25` | A number of at least 0.001, in seconds. The connect and read timeout. |
| `REDIS_MEMOIZE_RETRY_AFTER` | `30` | A number of at least 0, in seconds. How long an instance leaves Redis alone after a failure. |
| `REDIS_MEMOIZE_MAX_SIZE` | `1048576` | An integer of at least 1, in bytes. Larger serialized values stay in RAM. |
| `REDIS_MEMOIZE_INCLUDE` | empty | Comma-separated `fnmatch` patterns of function names. When set, only matching functions use Redis. |
| `REDIS_MEMOIZE_EXCLUDE` | empty | Comma-separated `fnmatch` patterns of function names. Matching functions stay in RAM; exclusion wins over inclusion. |

The test suite parses this table and compares it with the code.

## Keys

Each value is stored under a key made of three parts, separated by colons:

`<prefix>:<function>:<hash>`

`prefix`
:   `REDIS_MEMOIZE_PREFIX`.

`function`
:   The dotted name of the cached function, such as `plone.app.layout.sitemap.sitemap.generate`.

`hash`
:   The SHA-1 of the key `plone.memoize` computed for the call.

## Related

- {doc}`/how-to-guides/configure`
- {doc}`/reference/api/config`
