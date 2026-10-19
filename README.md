<div align="center">
    <h1 align="center">collective.redismemoize</h1>
</div>
<div align="center">

[![PyPI](https://img.shields.io/pypi/v/collective.redismemoize)](https://pypi.org/project/collective.redismemoize/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/collective.redismemoize)](https://pypi.org/project/collective.redismemoize/)
[![PyPI - License](https://img.shields.io/pypi/l/collective.redismemoize)](https://pypi.org/project/collective.redismemoize/)
[![PyPI - Plone Versions](https://img.shields.io/pypi/frameworkversions/plone/collective.redismemoize)](https://pypi.org/project/collective.redismemoize/)
[![CI](https://github.com/collective/collective.redismemoize/actions/workflows/main.yml/badge.svg)](https://github.com/collective/collective.redismemoize/actions/workflows/main.yml)

</div>

Redis-backed storage for `plone.memoize`, shared across Plone instances, that keeps the values Redis can't safely store in each process's RAM cache.

Every Plone instance keeps its own `plone.memoize` RAM cache, so behind a load balancer each one computes the same cached values on its own, and a new instance starts cold.
`collective.redismemoize` stores those values in Redis or Valkey instead, where every instance reads them.
Values that are not plain data, such as content objects or anything holding a database connection, stay in the RAM cache, exactly where stock Plone keeps them.

📖 **Documentation:** https://collective.github.io/collective.redismemoize/

## Features

- ✅ Works for every `@ram.cache` function in Plone and in your add-ons, without changing them.
- 🔀 Routes each function on its own: plain data goes to Redis, anything else stays in RAM, and the reason is logged once.
- 🔒 Reads values back with a restricted unpickler that resolves only the classes plain data needs, so a write to Redis cannot run code in Plone.
- 🛟 Fails safe: when Redis is slow or down, a circuit breaker keeps every instance on its RAM cache until Redis answers again.
- 🎯 Include and exclude functions by pattern, and give your own functions their own TTL.
- 📊 A Manager-only `@redismemoize` REST API endpoint reports the status, routes and counters, and invalidates values after a deploy.
- 🧪 A test layer for add-ons, backed by `fakeredis`, to check that what your functions cache is shareable.
- 🔁 Tested against Redis 7 and Valkey 8.

Without configuration, the package changes nothing.

## Installation

Add `collective.redismemoize` to the dependencies of your Plone project, and install it.
With `plone.autoinclude`, the default in Plone 6, there is nothing else to load and no add-on to activate.

Then set one environment variable on every instance:

```shell
REDIS_MEMOIZE_URL=redis://redis:6379/0
```

Run Redis as a cache, on a private network: persistence off, a memory limit, and `allkeys-lru` eviction.
The [configuration guide](https://collective.github.io/collective.redismemoize/how-to-guides/configure.html) has a Docker Compose example, and the [configuration reference](https://collective.github.io/collective.redismemoize/reference/configuration.html) lists every variable.

## Compatibility

| Component | Versions |
| --- | --- |
| Plone | 6.1, 6.2 |
| Python | 3.10 to 3.14 |
| Redis | 4.0 and later; tested with 7.4 |
| Valkey | 7.2 and later; tested with 8 |

## Contribute

- [Issue tracker](https://github.com/collective/collective.redismemoize/issues)
- [Source code](https://github.com/collective/collective.redismemoize/)
- [Security policy](SECURITY.md)

You need [uv](https://docs.astral.sh/uv/), Make, Git, and Docker for the tests against real servers.

```shell
git clone git@github.com:collective/collective.redismemoize.git
cd collective.redismemoize
make install
make test
```

`make test` needs no container.
`make test-docker` runs the tests against Redis and Valkey containers.
`make help` lists every target.

## License

The project is licensed under GPLv2.

Redis is a registered trademark of Redis Ltd.
Any rights therein are reserved to Redis Ltd.
Any use by this project is for referential purposes only and does not indicate any sponsorship, endorsement or affiliation between Redis and this project.
