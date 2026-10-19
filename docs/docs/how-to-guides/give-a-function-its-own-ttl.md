(how-to-ttl)=

# Give a function its own TTL

<!-- source: src/collective/redismemoize/api.py (cache), tests/docs/snippets/ttl.py -->

This guide shows you how to cache a function of your own add-on for a lifetime other than the default.

`plone.memoize.ram.cache` has no way to say how long a value lives, so every value in Redis gets `REDIS_MEMOIZE_TTL`, a day by default.
`collective.redismemoize.api.cache` takes the same key function, plus a `ttl` in seconds:

```{literalinclude} ../../../tests/docs/snippets/ttl.py
:language: python
```

The value goes through the same chooser, the same checks, and the same routing as any other cached function.
`ttl` only matters when the value ends up in Redis.
In RAM, and on a site where the package is not configured, the decorator behaves like `ram.cache`.

`ttl` must be a positive integer; anything else raises `ValueError` when the module is imported.

## Check it

Call the function, then look its key up in Redis:

```shell
redis-cli --scan --pattern 'plone.memoize:*country_names:*'
redis-cli ttl <the key printed above>
```

## Related

- {doc}`/reference/api/api`
- {doc}`/concepts/per-function-routing`
