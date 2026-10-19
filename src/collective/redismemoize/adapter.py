"""The cache adapter ``plone.memoize`` reads and writes through.

``plone.memoize.volatile.cache`` needs a mapping with ``get``,
``__getitem__`` and ``__setitem__``. :class:`RedisCacheAdapter` provides
them for one cached function, and decides per value where it goes:

- plain data, within the size limit, goes to Redis with a TTL;
- anything else goes to the stock RAM cache it wraps, and a refusal routes the
  whole function to RAM for the rest of the process;
- a Redis failure is a miss, never an error, and opens the circuit breaker.

A read asks Redis first and the RAM cache after a Redis miss, because a value
too large for Redis, or stored while the breaker was open, lives in RAM.

Values read from Redis are copies. A caller that mutates a cached value no
longer mutates the cache, which the RAM cache allowed.
"""

from collective.redismemoize.client import Connection
from collective.redismemoize.client import ERRORS
from collective.redismemoize.config import Settings
from collective.redismemoize.routing import Route
from collective.redismemoize.routing import Router
from collective.redismemoize.serializer import dumps
from collective.redismemoize.serializer import loads
from collective.redismemoize.serializer import NotShareable
from collective.redismemoize.serializer import UndecodableValue
from plone.memoize.ram import AbstractDict
from plone.memoize.ram import RAMCacheAdapter

import hashlib


def hash_key(key: str | bytes) -> str:
    """Hash a cache key the way ``plone.memoize`` does.

    :param key: The key ``volatile.cache`` built.
    :returns: Its SHA-1, in hex.
    """
    if isinstance(key, str):
        key = key.encode("utf-8")
    return hashlib.sha1(key, usedforsecurity=False).hexdigest()


class RedisCacheAdapter(AbstractDict):
    """Store one function's values in Redis, or in RAM when they cannot be.

    :param globalkey: Dotted name of the cached function.
    :param settings: The package settings.
    :param ram: The stock RAM adapter for the same function.
    :param router: Per-function routes and counters.
    :param connection: The Redis connection and its breaker.
    :param ttl: Lifetime of a stored value; ``settings.ttl`` when omitted.
    """

    def __init__(
        self,
        globalkey: str,
        settings: Settings,
        ram: RAMCacheAdapter,
        router: Router,
        connection: Connection,
        ttl: int | None = None,
    ):
        self.globalkey = globalkey
        self.settings = settings
        self.ram = ram
        self.router = router
        self.connection = connection
        self.ttl = settings.ttl if ttl is None else ttl

    def redis_key(self, key: str | bytes) -> str:
        """Return the Redis key of a cache key.

        :param key: The key ``volatile.cache`` built.
        :returns: ``<prefix>:<function>:<sha1 of key>``.
        """
        return f"{self.settings.prefix}:{self.globalkey}:{hash_key(key)}"

    def _uses_redis(self) -> bool:
        """Report whether this call may use Redis.

        :returns: ``False`` for a function routed to RAM, or while the breaker
            is open.
        """
        return (
            self.router.route_for(self.globalkey) is Route.REDIS
            and self.connection.available()
        )

    def _count(self, counter: str) -> None:
        """Add one to this function's counter.

        :param counter: Counter name.
        """
        self.router.count(self.globalkey, counter)

    def _ram_get(self, key: str | bytes) -> object:
        """Read the RAM cache.

        :param key: The cache key.
        :returns: The cached value.
        :raises KeyError: On a miss.
        """
        try:
            value = self.ram[key]
        except KeyError:
            self._count("ram_misses")
            raise
        self._count("ram_hits")
        return value

    def _ram_set(self, key: str | bytes, value: object) -> None:
        """Write the RAM cache.

        :param key: The cache key.
        :param value: The value.
        """
        self.ram[key] = value

    def __getitem__(self, key: str | bytes) -> object:
        """Return a cached value.

        :param key: The cache key.
        :returns: The value; a copy when it came from Redis.
        :raises KeyError: On a miss, including every kind of Redis failure.
        """
        if not self._uses_redis():
            return self._ram_get(key)
        try:
            payload = self.connection.client().get(self.redis_key(key))
        except ERRORS as exc:
            self.connection.failure(exc)
            self._count("errors")
            return self._ram_get(key)
        self.connection.success()
        if payload is None:
            # The value may be in RAM: too large for Redis, or stored while
            # the breaker was open.
            self._count("redis_misses")
            return self._ram_get(key)
        try:
            value = loads(payload)
        except UndecodableValue:
            self._count("undecodable")
            return self._ram_get(key)
        self._count("redis_hits")
        return value

    def __setitem__(self, key: str | bytes, value: object) -> None:
        """Store a value, in Redis when it is plain data, in RAM otherwise.

        :param key: The cache key.
        :param value: The value.
        """
        if not self._uses_redis():
            return self._ram_set(key, value)
        try:
            payload = dumps(value)
        except NotShareable as exc:
            self.router.learn(self.globalkey, Route.RAM_NOT_SHAREABLE, exc.reason)
            self._count("refused")
            return self._ram_set(key, value)
        if len(payload) > self.settings.max_size:
            self._count("too_large")
            return self._ram_set(key, value)
        try:
            self.connection.client().set(self.redis_key(key), payload, ex=self.ttl)
        except ERRORS as exc:
            self.connection.failure(exc)
            self._count("errors")
            return self._ram_set(key, value)
        self.connection.success()
        return None

    def __contains__(self, key: object) -> bool:
        """Report whether a value is cached.

        :param key: The cache key.
        :returns: Whether a lookup would hit.
        """
        try:
            self[key]  # type: ignore[index]
        except KeyError:
            return False
        return True

    def __delitem__(self, key: str | bytes) -> None:
        """Remove a value from Redis and from RAM; a missing key is no error.

        :param key: The cache key.
        """
        self.ram.ramcache.invalidate(
            self.ram.globalkey, {"key": self.ram._make_key(key)}
        )
        if not self._uses_redis():
            return
        try:
            self.connection.client().delete(self.redis_key(key))
        except ERRORS as exc:
            self.connection.failure(exc)
            self._count("errors")
            return
        self.connection.success()
