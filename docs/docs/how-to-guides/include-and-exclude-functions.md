(how-to-include-exclude)=

# Include and exclude functions

<!-- source: src/collective/redismemoize/config.py (Settings.exclusion_reason) -->

This guide shows you how to choose which cached functions may use Redis.

Functions are named by their dotted name, module then function: `plone.app.layout.sitemap.sitemap.generate`.
The status endpoint lists every function a process has seen, under `functions`.

## Keep some functions in RAM

Set `REDIS_MEMOIZE_EXCLUDE` to a comma-separated list of patterns:

```shell
REDIS_MEMOIZE_EXCLUDE=my.addon.browser.*,plone.app.event.*
```

Patterns use shell-style wildcards: `*` matches anything, `?` one character, and `[abc]` one of a set.
Matching is case sensitive.

## Allow only some functions into Redis

Set `REDIS_MEMOIZE_INCLUDE` the same way.
When it is set, only matching functions use Redis; all others stay in RAM.

```shell
REDIS_MEMOIZE_INCLUDE=plone.app.content.*,plone.app.layout.sitemap.*
```

## When both are set

A function matching an exclude pattern stays in RAM, even when it also matches an include pattern.
Exclusion always wins.

## Check it

Restart the instances, call the functions, and read the status endpoint.
An excluded function shows `"route": "ram-excluded"`, with the pattern that excluded it as `reason`.

## Related

- {doc}`/concepts/when-not-to-use`
- {doc}`/reference/configuration`
