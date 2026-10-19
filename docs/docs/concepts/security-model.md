(concepts-security)=

# Security model

<!-- source: src/collective/redismemoize/serializer.py, SECURITY.md -->

Everything in Redis is read back by every instance and turned into Python objects.
Whoever can write to Redis can therefore choose what every Plone process reads.

## The restricted reader

Values are stored as pickles, and an ordinary pickle can make the reading process call any function it names.
This package never reads one that way.
Its reader resolves only the classes plain data needs: `complex`, `Decimal`, the `datetime` types, `DateTime`, and `UUID`.
Anything else in a payload makes it unreadable, the read is a miss, and nothing named in it runs.
A test feeds it a payload that calls `os.system`, and checks that the command never ran.

So a write to Redis cannot run code in Plone.
It can still poison the cache: a value written under a function's key is served as that function's result until it expires.

## Keep Redis private

That is why Redis belongs on a network only the Plone instances reach.
In Docker Compose or Swarm, put it on an internal network and publish no port.
Add a password, or TLS with `rediss://`, when the network is shared with anything else.
{doc}`/how-to-guides/configure` shows the setup.

## One prefix per stack

Several sites, or several stacks, can share one Redis server, each with its own `REDIS_MEMOIZE_PREFIX`.
The prefix separates their values; it is not access control.
Stacks that must not read each other's values need separate servers, or separate Redis users with key patterns.

## What is in the values

The values are whatever Plone's cached functions return: translated strings, rendered portlets, the sitemap.
Most of it is public, but some cached HTML is rendered for an authenticated user.
Treat the Redis server as you treat the database server.

## Related

- [Security policy](https://github.com/collective/collective.redismemoize/blob/main/SECURITY.md)
- {doc}`what-shareable-means`
