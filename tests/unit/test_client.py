"""The lazy, fork-aware client and its circuit breaker."""

from collective.redismemoize import client as client_module
from collective.redismemoize import config
from collective.redismemoize.client import Connection
from collective.redismemoize.client import default_factory
from collective.redismemoize.config import Settings

import logging
import pytest
import redis


LOGGER = "collective.redismemoize"


@pytest.fixture
def built() -> list:
    """Collect the settings each client was built for."""
    return []


@pytest.fixture
def counting(settings, clock, built) -> Connection:
    """A connection whose factory records every client it builds."""

    def factory(s):
        built.append(s)
        return object()

    return Connection(settings, factory=factory, clock=clock)


class TestClient:
    def test_lazy(self, counting, built):
        """Nothing is built until the client is asked for."""
        assert built == []
        counting.client()
        assert len(built) == 1

    def test_reused(self, counting, built):
        """The same process gets the same client."""
        assert counting.client() is counting.client()
        assert len(built) == 1

    def test_recreated_after_fork(self, counting, built, monkeypatch):
        """A different process id gets a new client."""
        first = counting.client()
        monkeypatch.setattr(client_module.os, "getpid", lambda: -1)
        second = counting.client()
        assert second is not first
        assert len(built) == 2
        assert counting.client() is second

    def test_default_factory(self):
        """redis-py is configured from the settings, without connecting."""
        settings = Settings(url="redis://:pw@cache.example.org:6390/3", timeout=0.5)
        client = default_factory(settings)
        kwargs = client.connection_pool.connection_kwargs
        assert isinstance(client, redis.Redis)
        assert kwargs["host"] == "cache.example.org"
        assert kwargs["port"] == 6390
        assert kwargs["db"] == 3
        assert kwargs["password"] == "pw"
        assert kwargs["socket_timeout"] == 0.5
        assert kwargs["socket_connect_timeout"] == 0.5
        assert kwargs["health_check_interval"] == 30


class TestBreaker:
    def test_starts_closed(self, connection):
        """A new connection may call Redis."""
        assert connection.available() is True
        assert connection.is_open is False
        assert connection.seconds_until_retry() == 0.0

    def test_opens_on_failure(self, connection):
        """A failure makes Redis unavailable."""
        connection.failure(redis.ConnectionError("down"))
        assert connection.available() is False
        assert connection.is_open is True
        assert connection.seconds_until_retry() == 30.0

    def test_stays_open_for_retry_after(self, connection, clock):
        """Redis stays out of reach for ``retry_after`` seconds."""
        connection.failure(redis.ConnectionError("down"))
        clock.advance(29.9)
        assert connection.available() is False
        assert connection.seconds_until_retry() == pytest.approx(0.1)
        clock.advance(0.1)
        assert connection.available() is True

    def test_half_open_stays_open_until_success(self, connection, clock):
        """After the wait, Redis may be tried, but the breaker is not closed."""
        connection.failure(redis.ConnectionError("down"))
        clock.advance(31)
        assert connection.available() is True
        assert connection.is_open is True

    def test_failure_in_half_open_restarts_the_wait(self, connection, clock):
        """A failed retry keeps Redis out of reach for another period."""
        connection.failure(redis.ConnectionError("down"))
        clock.advance(31)
        connection.failure(redis.ConnectionError("still down"))
        assert connection.available() is False
        assert connection.seconds_until_retry() == 30.0

    def test_success_closes(self, connection, clock):
        """A success closes the breaker."""
        connection.failure(redis.ConnectionError("down"))
        clock.advance(31)
        connection.success()
        assert connection.is_open is False
        assert connection.available() is True

    def test_zero_retry_after(self, clock):
        """With ``retry_after`` 0, every call may try Redis again."""
        connection = Connection(Settings(url="redis://x", retry_after=0), clock=clock)
        connection.failure(OSError("down"))
        assert connection.available() is True
        assert connection.is_open is True


class TestLogging:
    def test_one_warning_when_opening(self, connection, clock, caplog):
        """Opening logs one warning, however many failures follow."""
        caplog.set_level(logging.INFO, logger=LOGGER)
        for _ in range(5):
            connection.failure(redis.ConnectionError("down"))
            clock.advance(31)
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "ConnectionError: down" in warnings[0].getMessage()
        assert "30" in warnings[0].getMessage()

    def test_one_info_when_closing(self, connection, caplog):
        """Closing logs one info line; successes while closed log nothing."""
        caplog.set_level(logging.INFO, logger=LOGGER)
        connection.success()
        connection.failure(redis.ConnectionError("down"))
        connection.success()
        connection.success()
        infos = [r for r in caplog.records if r.levelno == logging.INFO]
        assert [r.getMessage() for r in infos] == [
            "Redis available again; values are shared again"
        ]


class TestProcessConnection:
    @pytest.fixture(autouse=True)
    def _restore(self):
        yield
        client_module.set_factory(None)
        config.reload()

    def test_follows_settings(self, monkeypatch):
        """A reload of the settings gives a new connection."""
        monkeypatch.setenv("REDIS_MEMOIZE_URL", "redis://one")
        config.reload()
        first = client_module.get_connection()
        assert client_module.get_connection() is first
        assert first.settings.url == "redis://one"
        monkeypatch.setenv("REDIS_MEMOIZE_URL", "redis://two")
        config.reload()
        second = client_module.get_connection()
        assert second is not first
        assert second.settings.url == "redis://two"

    def test_set_factory(self):
        """``set_factory`` replaces the factory and drops the connection."""
        first = client_module.get_connection()
        marker = object()
        client_module.set_factory(lambda s: marker)
        second = client_module.get_connection()
        assert second is not first
        assert second.client() is marker
        client_module.set_factory(None)
        assert client_module.get_connection().factory is default_factory

    def test_reset(self):
        """``reset`` drops the connection."""
        first = client_module.get_connection()
        client_module.reset()
        assert client_module.get_connection() is not first
