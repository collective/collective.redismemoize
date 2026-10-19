(how-to-configure)=

# Configure Redis for a deployment

<!-- source: src/collective/redismemoize/config.py, tests/docs/snippets/docker-compose.yml -->

This guide shows you how to point Plone at a Redis server and run that server the way a shared cache needs.

## Set the URL

Set `REDIS_MEMOIZE_URL` in the environment of every Plone instance:

```shell
REDIS_MEMOIZE_URL=redis://redis:6379/0
```

The URL accepts the `redis://`, `rediss://` (TLS), and `unix://` schemes, as redis-py does.
Put a password in it when the server requires one: `redis://:secret@redis:6379/0`.
The status endpoint and the logs never show the password.

Give every instance of one site the same URL and the same `REDIS_MEMOIZE_PREFIX`.
Give different sites, or different stacks sharing one server, different prefixes.

{doc}`/reference/configuration` lists every variable.
Plone reads them once, at startup, and refuses to start when one is invalid, naming the variable.

## Run Redis as a cache

A cache holds nothing worth keeping across a restart, and must never fill the server's memory.
Start Redis with persistence off and a memory limit, evicting the least recently used keys:

- `--save ''` and `--appendonly no` turn persistence off;
- `--maxmemory` sets the limit;
- `--maxmemory-policy allkeys-lru` makes Redis evict old values instead of refusing new ones.

## Keep it on a private network

Only the Plone instances need to reach Redis.
In Docker Compose or Swarm, put Redis on an internal network, publish no port, and connect the backend to that network:

```{literalinclude} ../../../tests/docs/snippets/docker-compose.yml
:language: yaml
```

The test suite parses this file and checks each of these properties.

If anything else shares the network, add `--requirepass` to the Redis command and the password to the URL, or use TLS with `rediss://`.
{doc}`/concepts/security-model` explains why this matters.

## Check it

Request the status endpoint as a Manager on any instance.
`active` is `true`, `server.version` shows the Redis version, and `breaker.open` is `false`.

## Next steps

- {doc}`monitor`
- {doc}`use-valkey`
- {doc}`include-and-exclude-functions`
