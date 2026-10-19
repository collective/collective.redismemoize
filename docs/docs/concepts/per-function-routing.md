(concepts-routing)=

# Per-function routing

<!-- source: src/collective/redismemoize/routing.py, src/collective/redismemoize/adapter.py -->

Every cached function has a {term}`route`, which says where its values go.

`redis`
:   The default. Values that are plain data go to Redis.

`ram-excluded`
:   The configuration keeps the function in RAM, through `REDIS_MEMOIZE_EXCLUDE` or `REDIS_MEMOIZE_INCLUDE`.

`ram-not-shareable`
:   One of the function's values was not plain data, so all of its values stay in RAM.

## Why a refusal routes the whole function

A function that returned a content object once will return one again.
Trying Redis for each of its values would pay for a serialization attempt and a refusal on every miss, only to end up in RAM anyway.
So the first refusal routes the function to RAM for the rest of the process, and the log says so once, at `INFO`, with the reason.

The route is learned per process and forgotten at restart.
A deploy that changes what a function returns therefore gets a fresh decision.

## Why size is decided per value

Values larger than `REDIS_MEMOIZE_MAX_SIZE` also stay in RAM, but only that value.
The size of a function's result varies from call to call, while its type rarely does.
One large sitemap says nothing about the next, smaller one.

## Reads look in both places

A read asks Redis first.
On a Redis miss it asks the RAM cache, because a value too large for Redis, or stored while Redis was unreachable, lives there.
A function routed to RAM never reaches Redis at all.

## The counters

For every function it has seen, each process counts Redis hits and misses, RAM hits and misses, refusals, values too large, payloads it could not decode, and Redis errors.
The status endpoint shows them next to the route.

They are there for the one judgment this package cannot make.
A value can be plain data and still be wrong to share, when its cache key leaves out something that differs between instances.
{doc}`when-not-to-use` describes how to spot one.

## Related

- {doc}`/how-to-guides/include-and-exclude-functions`
- {doc}`/how-to-guides/monitor`
- {doc}`/reference/rest-api`
