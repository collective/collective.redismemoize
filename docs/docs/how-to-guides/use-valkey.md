(how-to-use-another-server)=

# Use Valkey instead of Redis

<!-- source: tests/docker/test_servers.py, src/collective/redismemoize/api.py -->

This guide shows you how to use {term}`Valkey` as the cache server.

Valkey speaks the Redis protocol, and the package talks to it with the same client and the same `redis://` URL.
The test suite runs the same tests against Redis 7 and Valkey 8.

## Run Valkey

Replace the Redis image and command with Valkey's:

```yaml
services:
  redis:
    image: valkey/valkey:8-alpine
    command:
      - valkey-server
      - --save
      - ''
      - --appendonly
      - 'no'
      - --maxmemory
      - 256mb
      - --maxmemory-policy
      - allkeys-lru
    networks:
      - cache
```

Keep `REDIS_MEMOIZE_URL` as it was: the scheme stays `redis://`.

## Check it

The status endpoint reports `"product": "valkey"` and Valkey's version under `server`.

## Related

- {doc}`configure`
- {doc}`/reference/compatibility`
