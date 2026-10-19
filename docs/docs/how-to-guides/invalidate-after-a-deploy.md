(how-to-invalidate)=

# Invalidate cached values after a deploy

<!-- source: src/collective/redismemoize/api.py (invalidate, invalidate_all), src/collective/redismemoize/services/__init__.py -->

This guide shows you how to drop cached values when a deploy changes what a cached function returns.

Values in Redis outlive the processes that stored them.
When new code computes a different value for the same key, the old value stays in Redis until its TTL runs out, and every instance keeps serving it.
Nothing in the package invalidates on its own; you decide when.

## Drop one function's values

Send a `POST` to the `@redismemoize/invalidate` endpoint of the site, as a Manager, naming the function:

```shell
curl -u admin:admin -X POST \
  -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{"function": "my.addon.vocabularies.country_names"}' \
  http://localhost:8080/Plone/@redismemoize/invalidate
```

The response gives the number of Redis keys removed.
The RAM cache of the instance that answered is cleared for that function too.

## Drop everything under the prefix

Send the same request with an empty object as the body:

```shell
curl -u admin:admin -X POST \
  -H "Accept: application/json" -H "Content-Type: application/json" \
  -d '{}' \
  http://localhost:8080/Plone/@redismemoize/invalidate
```

This removes every key under `REDIS_MEMOIZE_PREFIX`, and empties the RAM cache of the instance that answered.

## Invalidate from Python

From an upgrade step, or a script run with `zconsole`, call the API directly:

```python
from collective.redismemoize import api

api.invalidate("my.addon.vocabularies.country_names")
api.invalidate_all()
```

## The RAM caches of other instances

Invalidation reaches Redis and the RAM cache of the process that runs it.
The other instances still hold the values they keep in RAM: values refused by Redis, and values of excluded functions.
A rolling restart empties those; a deploy usually restarts every instance anyway.

## Change the prefix instead

When a deploy changes many cached functions at once, you can also change `REDIS_MEMOIZE_PREFIX` in the same deploy.
The new instances never see the old keys, and Redis evicts them as memory fills, or when their TTL runs out.

## Related

- {doc}`/reference/rest-api`
- {doc}`/reference/api/api`
