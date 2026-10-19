---
myst:
  html_meta:
    "description": "Terms used throughout the collective.redismemoize documentation."
    "property=og:description": "Terms used throughout the collective.redismemoize documentation."
    "property=og:title": "Glossary"
    "keywords": "Plone, plone.memoize, Redis, glossary"
---

(glossary)=

# Glossary

```{glossary}
:sorted: true

cache chooser
    The `ICacheChooser` utility `plone.memoize` asks for the cache of each cached function.
    This package registers its own in place of the stock one.

cache key
    The string `plone.memoize` builds from the function's dotted name and the result of its key function.
    Two calls with the same cache key get the same value.

circuit breaker
    The mechanism that stops calling Redis for a while after a failure, so an outage costs one timeout rather than one per request.

plain data
    A value built only from strings, numbers, dates, UUIDs, and lists, tuples, sets, and dictionaries of those.
    Only plain data is stored in Redis.

RAM cache
    The process-local `zope.ramcache` cache stock Plone uses for `@ram.cache` functions.

route
    Where a cached function's values go: `redis`, `ram-excluded`, or `ram-not-shareable`.

Valkey
    An open source fork of Redis, compatible with its protocol.
```
