"""The Redis connection: created lazily, per process, behind a circuit breaker.

The client is created on first use and recreated when the process id
changes, so a server that forks workers after startup never shares a socket
between processes.

The breaker is what keeps a Redis outage from becoming a Plone outage. After
a failure, :meth:`Connection.available` is ``False`` for ``retry_after``
seconds and every cached function goes straight to its RAM cache, without
waiting for a timeout per call. The first call after that tries Redis again;
a success closes the breaker, a failure keeps it open for another period.
One ``WARNING`` is logged when the breaker opens and one ``INFO`` when it
closes, never one line per request.

This module is pure Python and never imports Zope.
"""

from collections.abc import Callable
from collective.redismemoize import logger
from collective.redismemoize.config import get_settings
from collective.redismemoize.config import Settings
from typing import Any

import os
import redis
import threading
import time


#: The exceptions that mean Redis, or the network to it, failed.
ERRORS: tuple[type[BaseException], ...] = (redis.RedisError, OSError)

#: Builds a client from the settings. Replaced by tests and by
#: :mod:`collective.redismemoize.testing` to point at ``fakeredis``.
ClientFactory = Callable[[Settings], Any]


def default_factory(settings: Settings) -> redis.Redis:
    """Create a redis-py client for the configured URL.

    :param settings: The package settings.
    :returns: A client; no connection is opened until the first command.
    """
    return redis.Redis.from_url(
        settings.url,
        socket_timeout=settings.timeout,
        socket_connect_timeout=settings.timeout,
        health_check_interval=30,
    )


class Connection:
    """A lazily created client and the circuit breaker in front of it.

    :param settings: The package settings.
    :param factory: Builds the client.
    :param clock: Monotonic clock, in seconds; injectable for tests.
    """

    def __init__(
        self,
        settings: Settings,
        factory: ClientFactory = default_factory,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.settings = settings
        self.factory = factory
        self.clock = clock
        self._client: Any = None
        self._pid: int | None = None
        self._failed_at: float | None = None
        self._lock = threading.Lock()

    def client(self) -> Any:
        """Return the client for this process, creating it if needed.

        :returns: The client.
        """
        pid = os.getpid()
        with self._lock:
            if self._client is None or self._pid != pid:
                self._client = self.factory(self.settings)
                self._pid = pid
            return self._client

    @property
    def is_open(self) -> bool:
        """Report whether the breaker is open, whatever the time.

        :returns: ``True`` from a failure until the next success.
        """
        return self._failed_at is not None

    def seconds_until_retry(self) -> float:
        """Return how long the breaker keeps Redis out of reach.

        :returns: Seconds until the next attempt; ``0`` when closed or due.
        """
        if self._failed_at is None:
            return 0.0
        return max(0.0, self.settings.retry_after - (self.clock() - self._failed_at))

    def available(self) -> bool:
        """Report whether Redis may be called now.

        :returns: ``False`` while the breaker waits out ``retry_after``.
        """
        return self.seconds_until_retry() == 0.0

    def failure(self, exc: BaseException) -> None:
        """Record a failed call, opening the breaker.

        :param exc: What went wrong, for the log.
        """
        with self._lock:
            opened = self._failed_at is None
            self._failed_at = self.clock()
        if opened:
            logger.warning(
                "Redis unavailable (%s: %s); using the RAM cache for %ss",
                type(exc).__name__,
                exc,
                self.settings.retry_after,
            )

    def success(self) -> None:
        """Record a successful call, closing the breaker if it was open."""
        if self._failed_at is None:
            return
        with self._lock:
            self._failed_at = None
        logger.info("Redis available again; values are shared again")


_connection: Connection | None = None
_factory: ClientFactory = default_factory


def get_connection() -> Connection:
    """Return the process connection, matching the current settings.

    :returns: The connection; a new one when the settings were reloaded.
    """
    global _connection
    settings = get_settings()
    if _connection is None or _connection.settings is not settings:
        _connection = Connection(settings, factory=_factory)
    return _connection


def set_factory(factory: ClientFactory | None) -> None:
    """Replace the client factory, and drop the current connection.

    :param factory: The new factory; ``None`` restores redis-py.
    """
    global _connection, _factory
    _factory = default_factory if factory is None else factory
    _connection = None


def reset() -> None:
    """Drop the current connection; the next call creates a new one."""
    global _connection
    _connection = None
