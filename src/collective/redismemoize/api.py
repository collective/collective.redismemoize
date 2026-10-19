"""Public API: invalidation, status, and a decorator with its own TTL.

Nothing in this package calls :func:`invalidate_all` on its own. Call it when
the meaning of cached values changes for every instance at once, typically
after a deploy that changes what a cached function returns, or from an
upgrade step.
"""

from collections.abc import Callable
from collective.redismemoize.adapter import RedisCacheAdapter
from collective.redismemoize.client import ERRORS
from collective.redismemoize.client import get_connection
from collective.redismemoize.config import get_settings
from collective.redismemoize.routing import router
from plone.memoize import volatile
from plone.memoize.ram import global_cache
from plone.memoize.ram import store_in_cache
from typing import Any
from zope.component import queryUtility
from zope.ramcache.interfaces.ram import IRAMCache

import re
import redis
import time


#: How many keys one ``SCAN`` step asks for, and one ``UNLINK`` removes.
BATCH_SIZE = 500


def _escape(text: str) -> str:
    """Escape the glob characters Redis ``MATCH`` patterns understand.

    :param text: Literal text.
    :returns: The text, matching only itself.
    """
    return re.sub(r"([*?\[\]\\])", r"\\\1", text)


def _unlink(pattern: str) -> int:
    """Remove every Redis key matching a pattern, in batches.

    :param pattern: A ``MATCH`` pattern.
    :returns: How many keys were removed; ``0`` when Redis is unreachable.
    """
    connection = get_connection()
    removed = 0
    try:
        client = connection.client()
        batch: list[Any] = []
        for key in client.scan_iter(match=pattern, count=BATCH_SIZE):
            batch.append(key)
            if len(batch) == BATCH_SIZE:
                removed += client.unlink(*batch)
                batch = []
        if batch:
            removed += client.unlink(*batch)
    except ERRORS as exc:
        connection.failure(exc)
        return removed
    connection.success()
    return removed


def ram_caches() -> list[Any]:
    """Return the RAM caches ``plone.memoize`` may have stored values in.

    The chooser wraps the ``IRAMCache`` utility, while ``store_in_cache``
    falls back to ``global_cache`` when no chooser is registered. They are
    usually the same object, but not always: a test layer can register its own.

    :returns: ``global_cache``, and the utility when it is a different cache.
    """
    caches = [global_cache]
    utility = queryUtility(IRAMCache)
    if utility is not None and utility is not global_cache:
        caches.append(utility)
    return caches


def invalidate(fun_name: str) -> int:
    """Drop every cached value of one function, in Redis and in RAM.

    :param fun_name: Dotted name of the cached function, as
        ``module.function``.
    :returns: How many Redis keys were removed.
    """
    for cache in ram_caches():
        cache.invalidate(fun_name)
    settings = get_settings()
    if not settings.active:
        return 0
    return _unlink(f"{_escape(settings.prefix)}:{_escape(fun_name)}:*")


def invalidate_all() -> int:
    """Drop every cached value under the prefix, and the whole RAM cache.

    :returns: How many Redis keys were removed.
    """
    for cache in ram_caches():
        cache.invalidateAll()
    settings = get_settings()
    if not settings.active:
        return 0
    return _unlink(f"{_escape(settings.prefix)}:*")


def _server() -> dict[str, Any]:
    """Ask the server for its latency and version.

    :returns: ``latency_ms``, ``product``, ``version`` and ``error``.
    """
    connection = get_connection()
    info: dict[str, Any] = {
        "latency_ms": None,
        "product": None,
        "version": None,
        "error": None,
    }
    try:
        client = connection.client()
        started = time.perf_counter()
        client.ping()
        info["latency_ms"] = round((time.perf_counter() - started) * 1000, 3)
        try:
            server = client.info("server")
        except redis.ResponseError:
            # The server answered, but refuses INFO: some managed services
            # rename or disable it. That is not an outage.
            server = {}
    except ERRORS as exc:
        connection.failure(exc)
        info["error"] = f"{type(exc).__name__}: {exc}"
        return info
    connection.success()
    if "valkey_version" in server:
        info["product"] = "valkey"
        info["version"] = str(server["valkey_version"])
    else:
        info["product"] = "redis"
        version = server.get("redis_version")
        info["version"] = None if version is None else str(version)
    return info


def status() -> dict[str, Any]:
    """Describe the configuration, the breaker, the server and the routes.

    This contacts Redis (a ``PING`` and an ``INFO server``) even while the
    breaker is open, so it reports the server's current state.

    :returns: A JSON-serializable mapping.
    """
    settings = get_settings()
    result: dict[str, Any] = {
        "active": settings.active,
        "settings": {
            "url": settings.redacted_url,
            "prefix": settings.prefix,
            "ttl": settings.ttl,
            "timeout": settings.timeout,
            "retry_after": settings.retry_after,
            "max_size": settings.max_size,
            "include": list(settings.include),
            "exclude": list(settings.exclude),
        },
        "breaker": None,
        "server": None,
        "functions": router.snapshot(),
    }
    if settings.active:
        connection = get_connection()
        result["server"] = _server()
        result["breaker"] = {
            "open": connection.is_open,
            "seconds_until_retry": round(connection.seconds_until_retry(), 3),
        }
    return result


def cache(get_key: Callable[..., Any], ttl: int | None = None) -> Callable:
    """Decorate a function like ``plone.memoize.ram.cache``, with its own TTL.

    The value goes through the same chooser, serializer and routing as any
    other cached function; ``ttl`` only matters when it ends up in Redis.

    :param get_key: Builds the cache key, as for ``plone.memoize.ram.cache``.
    :param ttl: Lifetime in seconds; the configured default when omitted.
    :returns: The decorator.
    :raises ValueError: When ``ttl`` is not a positive integer.
    """
    if ttl is not None and (type(ttl) is not int or ttl < 1):
        raise ValueError(f"ttl must be a positive integer, not {ttl!r}")

    def get_cache(fun: Callable, *args: Any, **kwargs: Any) -> Any:
        adapter = store_in_cache(fun, *args, **kwargs)
        if ttl is not None and isinstance(adapter, RedisCacheAdapter):
            adapter.ttl = ttl
        return adapter

    return volatile.cache(get_key, get_cache=get_cache)
