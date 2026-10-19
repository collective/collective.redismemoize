(how-to-monitor)=

# Monitor the cache

<!-- source: src/collective/redismemoize/api.py (status), src/collective/redismemoize/routing.py, src/collective/redismemoize/client.py -->

This guide shows you how to check that the cache works, and how to notice when it stops working.

## Read the status endpoint

Request `@redismemoize` on the site, as a Manager:

```shell
curl -u admin:admin -H "Accept: application/json" http://localhost:8080/Plone/@redismemoize
```

Each instance answers for itself: the breaker, the routes, and the counters belong to the process that handled the request.
Behind a load balancer, request each instance directly to compare them.

Look at these fields:

`active`
:   `false` means no URL is configured, and the package does nothing.

`server.error`
:   Set when the instance could not reach the server just now.

`breaker.open`
:   `true` while the instance leaves Redis alone after a failure; `seconds_until_retry` says for how long.

`functions`
:   Every cached function the process has seen, with its route and its counters.

{doc}`/reference/rest-api` describes every field.

## Read the counters

For a function routed to `redis`, `redis_hits` growing on an instance that never computed the value is what sharing looks like.
`ram_hits` and `ram_misses` count the values kept in RAM.

Watch these counters:

`refused`
:   Values that are not shareable; the function's route turned to `ram-not-shareable`.

`too_large`
:   Values larger than `REDIS_MEMOIZE_MAX_SIZE`; they were kept in RAM.

`undecodable`
:   Values in Redis that this instance could not read, usually written by another version of a package.

`errors`
:   Calls to Redis that failed.

## Watch the logs

The package logs to the `collective.redismemoize` logger.
Alert on its `WARNING` message, which the instance logs once each time it loses Redis.
{doc}`/reference/log-messages` lists every message.

## Watch the server

On the Redis side, watch memory use and evictions with `INFO memory` and `INFO stats`.
Evictions are expected once memory fills, with `allkeys-lru`; a cache that is always full may need a larger `--maxmemory`.

## Related

- {doc}`troubleshoot`
- {doc}`/concepts/failure-model`
