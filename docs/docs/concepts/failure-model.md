(concepts-failures)=

# Failure model

<!-- source: src/collective/redismemoize/client.py, src/collective/redismemoize/adapter.py -->

A cache must never be the reason a page fails.
Every Redis failure, from a refused connection to a timeout or a server that answers with an error, is treated as a miss.
The function runs, and its value goes to the RAM cache.

## Timeouts

Every connection and every command has a timeout, `REDIS_MEMOIZE_TIMEOUT`, a quarter of a second by default.
A cache that answers slower than that is not saving anything.

## The circuit breaker

A timeout per call would still turn an outage into slow pages, one timeout per cached call.
So after a failure, the process stops calling Redis for `REDIS_MEMOIZE_RETRY_AFTER` seconds, thirty by default, and every cached function uses its RAM cache.
This is the {term}`circuit breaker`.

When the wait is over, the next call tries Redis again.
A success closes the breaker and values are shared again; a failure starts another wait.
The log gets one `WARNING` when the breaker opens and one `INFO` when it closes, never one line per request.

Each process has its own breaker.
One instance losing its network path to Redis does not stop the others from using it.

## What is lost during an outage

Only sharing.
Each instance computes and caches its own values, as stock Plone does.
Values cached in RAM during the outage stay there until they expire, and a read finds them after a Redis miss.

## Payloads that cannot be read

A payload this version cannot decode, because it is corrupt or written in a future format, is a miss too.
That is not a server failure, so the breaker stays closed.

## Forked workers

The connection is created on first use and recreated when the process id changes, so a server that forks workers after startup never shares a socket between them.

## Related

- {doc}`/reference/log-messages`
- {doc}`/how-to-guides/troubleshoot`
- {doc}`/reference/configuration`
