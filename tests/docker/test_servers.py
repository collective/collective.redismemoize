"""Against real Redis and Valkey: sharing, expiry, invalidation, outages."""

from . import CLOSED_URL
from collective.redismemoize import api
from collective.redismemoize.adapter import RedisCacheAdapter
from collective.redismemoize.client import Connection
from collective.redismemoize.client import get_connection
from collective.redismemoize.config import Settings
from collective.redismemoize.routing import Router
from plone.memoize.ram import RAMCacheAdapter
from zope.ramcache.ram import RAMCache

import pytest
import redis
import time


pytestmark = pytest.mark.docker

FUN = "tests.docker.compute"


class Clock:
    """A clock the test moves by hand."""

    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def instance(settings: Settings, **kwargs) -> RedisCacheAdapter:
    """Build an adapter as one Plone instance would: its own RAM, router, client."""
    return RedisCacheAdapter(
        FUN,
        settings,
        RAMCacheAdapter(RAMCache(), globalkey=FUN),
        Router(),
        kwargs.pop("connection", None) or Connection(settings),
        **kwargs,
    )


class TestSharing:
    def test_two_instances_share_a_value(self, configured):
        """A value one instance stores is a hit in another."""
        first, second = instance(configured), instance(configured)
        first["key"] = {"lang": "en", "items": [1, 2]}
        assert second["key"] == {"lang": "en", "items": [1, 2]}

    def test_payload_on_the_server(self, configured, raw):
        """The value is stored under the documented key, with a TTL."""
        adapter = instance(configured)
        adapter["key"] = "x"
        assert raw.get(adapter.redis_key("key"))[:1] == b"\x01"
        assert 0 < raw.ttl(adapter.redis_key("key")) <= configured.ttl


class TestExpiry:
    def test_ttl_expires(self, configured):
        """A value with a one-second TTL is gone after it."""
        adapter = instance(configured, ttl=1)
        adapter["key"] = "short-lived"
        assert adapter["key"] == "short-lived"
        time.sleep(2.1)
        with pytest.raises(KeyError):
            adapter["key"]


class TestInvalidation:
    def test_invalidate_more_than_a_batch(self, configured, raw, prefix):
        """``invalidate`` removes every key of a function, across SCAN batches."""
        count = api.BATCH_SIZE * 2 + 37
        with raw.pipeline() as pipe:
            for index in range(count):
                pipe.set(f"{prefix}:{FUN}:{index}", b"x")
            pipe.set(f"{prefix}:other.function:0", b"keep")
            pipe.execute()
        assert api.invalidate(FUN) == count
        assert list(raw.scan_iter(match=f"{prefix}:*")) == [
            f"{prefix}:other.function:0".encode()
        ]

    def test_invalidate_all(self, configured, raw, prefix):
        """``invalidate_all`` removes the prefix and nothing else."""
        raw.set(f"{prefix}:a:1", b"x")
        raw.set(f"{prefix}:b:1", b"x")
        raw.set(f"{prefix}-not-ours:a:1", b"keep")
        assert api.invalidate_all() == 2
        assert raw.get(f"{prefix}-not-ours:a:1") == b"keep"
        raw.delete(f"{prefix}-not-ours:a:1")


class TestOutage:
    def test_closed_port(self):
        """A server that is not there: misses, RAM fallback, breaker open."""
        settings = Settings(url=CLOSED_URL, prefix="outage", timeout=0.5)
        adapter = instance(settings)
        assert adapter.get("key") is None
        assert adapter.connection.is_open
        adapter["key"] = "kept in RAM"
        assert adapter["key"] == "kept in RAM"

    def test_recovery(self, configured, server_url):
        """After ``retry_after``, the real server is used again."""
        clock = Clock()
        url = {"value": CLOSED_URL}

        def factory(settings):
            return redis.Redis.from_url(url["value"], socket_timeout=0.5)

        connection = Connection(configured, factory=factory, clock=clock)
        adapter = instance(configured, connection=connection)
        adapter["key"] = "during"
        assert connection.is_open
        url["value"] = server_url
        connection._client = None
        clock.now += configured.retry_after
        adapter["key"] = "after"
        assert connection.is_open is False
        assert instance(configured)["key"] == "after"


class TestStatus:
    def test_server_version(self, configured, product):
        """``status`` names the product and its version."""
        server = api.status()["server"]
        assert server["error"] is None
        assert server["product"] == product
        assert server["version"].split(".")[0].isdigit()
        assert server["latency_ms"] > 0

    def test_breaker_closed(self, configured):
        """A reachable server leaves the breaker closed."""
        api.status()
        assert get_connection().is_open is False
