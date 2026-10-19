"""The adapter ``plone.memoize`` reads and writes through, on ``fakeredis``."""

from collective.redismemoize.adapter import hash_key
from collective.redismemoize.client import Connection
from collective.redismemoize.config import Settings
from collective.redismemoize.routing import Route
from collective.redismemoize.serializer import FORMAT_VERSION
from persistent import Persistent
from tests import FUN_NAME
from tests import PREFIX

import hashlib
import pickle
import pytest
import redis


KEY = f"{FUN_NAME}:('en',)"


class Thing(Persistent):
    """Not plain data."""


class FailingClient:
    """A client whose every command fails, and that counts the attempts."""

    def __init__(self, exc: Exception):
        self.exc = exc
        self.calls: list[str] = []

    def _fail(self, name: str):
        self.calls.append(name)
        raise self.exc

    def get(self, *args, **kwargs):
        return self._fail("get")

    def set(self, *args, **kwargs):
        return self._fail("set")

    def delete(self, *args, **kwargs):
        return self._fail("delete")


@pytest.fixture(
    params=[redis.ConnectionError("down"), redis.TimeoutError("slow"), OSError("reset")]
)
def failing(request) -> FailingClient:
    """A failing client, for each kind of failure."""
    return FailingClient(request.param)


@pytest.fixture
def broken(make_adapter, settings, clock, failing):
    """An adapter whose Redis always fails."""
    connection = Connection(settings, factory=lambda s: failing, clock=clock)
    return make_adapter(connection=connection)


def counters(adapter) -> dict:
    """Return the adapter's function counters."""
    return adapter.router.snapshot()[adapter.globalkey]["counters"]


class TestKeys:
    def test_redis_key(self, adapter):
        """Keys are prefix, function and the SHA-1 of the cache key."""
        digest = hashlib.sha1(KEY.encode("utf-8"), usedforsecurity=False).hexdigest()
        assert adapter.redis_key(KEY) == f"{PREFIX}:{FUN_NAME}:{digest}"

    def test_bytes_and_str_hash_alike(self):
        """A str key and its UTF-8 bytes are the same key."""
        assert hash_key("ã") == hash_key("ã".encode())

    def test_two_functions_do_not_collide(self, make_adapter):
        """The same cache key under two functions is two Redis keys."""
        assert make_adapter("a.f").redis_key(KEY) != make_adapter("a.g").redis_key(KEY)


class TestRedisRoundTrip:
    def test_miss(self, adapter):
        """An empty cache raises KeyError, and ``get`` returns the default."""
        with pytest.raises(KeyError):
            adapter[KEY]
        assert adapter.get(KEY, "default") == "default"
        assert counters(adapter)["redis_misses"] == 2
        assert counters(adapter)["ram_misses"] == 2

    def test_redis_miss_reads_ram(self, adapter):
        """A Redis miss falls back to the RAM cache."""
        adapter.ram[KEY] = "from ram"
        assert adapter[KEY] == "from ram"
        assert counters(adapter)["redis_misses"] == 1
        assert counters(adapter)["ram_hits"] == 1

    def test_set_then_get(self, adapter, inspector):
        """A plain value is stored in Redis and read back."""
        adapter[KEY] = {"lang": "en"}
        assert adapter[KEY] == {"lang": "en"}
        assert inspector.get(adapter.redis_key(KEY))[:1] == FORMAT_VERSION
        assert counters(adapter)["redis_hits"] == 1

    def test_not_in_ram(self, adapter):
        """A value stored in Redis is not also kept in RAM."""
        adapter[KEY] = "x"
        with pytest.raises(KeyError):
            adapter.ram[KEY]

    def test_ttl(self, adapter, inspector, settings):
        """Values expire after the configured TTL."""
        adapter[KEY] = "x"
        ttl = inspector.ttl(adapter.redis_key(KEY))
        assert settings.ttl - 5 <= ttl <= settings.ttl

    def test_custom_ttl(self, make_adapter, inspector):
        """An adapter built with a TTL uses it."""
        adapter = make_adapter(ttl=42)
        adapter[KEY] = "x"
        assert 37 <= inspector.ttl(adapter.redis_key(KEY)) <= 42

    def test_values_are_copies(self, adapter):
        """Mutating a value read from Redis does not change the cache."""
        adapter[KEY] = {"items": [1]}
        first = adapter[KEY]
        first["items"].append(2)
        assert adapter[KEY] == {"items": [1]}

    def test_shared_between_adapters(self, make_adapter, ramcache):
        """Two adapters, as two instances would build them, share a value."""
        from collective.redismemoize.routing import Router
        from plone.memoize.ram import RAMCacheAdapter
        from zope.ramcache.ram import RAMCache

        writer = make_adapter()
        reader = make_adapter(
            ram=RAMCacheAdapter(RAMCache(), globalkey=FUN_NAME), router=Router()
        )
        writer[KEY] = ["shared"]
        assert reader[KEY] == ["shared"]

    def test_contains(self, adapter):
        """``in`` reports whether a lookup would hit."""
        assert KEY not in adapter
        adapter[KEY] = 0
        assert KEY in adapter

    def test_delitem(self, adapter, inspector):
        """Deleting removes the value from Redis."""
        adapter[KEY] = "x"
        del adapter[KEY]
        assert inspector.get(adapter.redis_key(KEY)) is None
        assert KEY not in adapter

    def test_delitem_missing(self, adapter):
        """Deleting a key that is not cached is no error."""
        del adapter[KEY]

    def test_falsy_values(self, adapter):
        """``None``, ``0`` and empty values are hits, not misses."""
        for value in (None, 0, "", [], {}):
            adapter[KEY] = value
            assert adapter[KEY] == value


class TestNotShareable:
    def test_goes_to_ram(self, adapter, inspector):
        """A value that is not plain data is kept in RAM, not in Redis."""
        thing = Thing()
        adapter[KEY] = thing
        assert adapter[KEY] is thing
        assert inspector.keys("*") == []

    def test_route_learned(self, adapter):
        """One refusal routes the whole function to RAM."""
        adapter[KEY] = Thing()
        assert adapter.router.route_for(FUN_NAME) is Route.RAM_NOT_SHAREABLE
        assert "Thing" in adapter.router.snapshot()[FUN_NAME]["reason"]
        assert counters(adapter)["refused"] == 1

    def test_route_is_sticky(self, adapter, inspector):
        """After a refusal, even plain values of the function stay in RAM."""
        adapter[KEY] = Thing()
        adapter["other"] = "plain"
        assert adapter["other"] == "plain"
        assert inspector.keys("*") == []
        assert counters(adapter)["refused"] == 1

    def test_route_skips_redis(self, make_adapter, settings, clock, router):
        """A function routed to RAM never calls Redis again."""
        spy = FailingClient(redis.ConnectionError("should not be called"))
        adapter = make_adapter(
            connection=Connection(settings, factory=lambda s: spy, clock=clock)
        )
        router.learn(FUN_NAME, Route.RAM_NOT_SHAREABLE, "x")
        adapter[KEY] = "plain"
        assert adapter[KEY] == "plain"
        del adapter[KEY]
        assert spy.calls == []

    def test_other_functions_unaffected(self, make_adapter, inspector):
        """A refusal in one function does not route another."""
        make_adapter("a.f")[KEY] = Thing()
        other = make_adapter("a.g")
        other[KEY] = "plain"
        assert inspector.get(other.redis_key(KEY)) is not None


class TestTooLarge:
    @pytest.fixture
    def small(self, make_adapter):
        """An adapter whose limit is 100 bytes."""
        return make_adapter(
            settings=Settings(url="redis://x", prefix=PREFIX, max_size=100)
        )

    def test_large_value_in_ram(self, small, inspector):
        """A value over the limit goes to RAM."""
        small[KEY] = "x" * 200
        assert small[KEY] == "x" * 200
        assert inspector.keys("*") == []
        assert counters(small)["too_large"] == 1

    def test_decided_per_value(self, small, inspector):
        """The next, smaller value of the same function goes to Redis."""
        small[KEY] = "x" * 200
        small["other"] = "small"
        assert inspector.get(small.redis_key("other")) is not None
        assert small.router.route_for(FUN_NAME) is Route.REDIS

    def test_limit_is_inclusive(self, small, inspector):
        """A payload exactly at the limit goes to Redis."""
        payload_overhead = len(FORMAT_VERSION + pickle.dumps("", protocol=5))
        small[KEY] = "x" * (100 - payload_overhead)
        assert inspector.get(small.redis_key(KEY)) is not None


class TestFailures:
    def test_get_error_is_a_miss(self, broken):
        """A Redis error on read is a miss, not an exception."""
        with pytest.raises(KeyError):
            broken[KEY]
        assert broken.connection.is_open
        assert counters(broken)["errors"] == 1

    def test_set_error_falls_back_to_ram(self, broken):
        """A Redis error on write stores the value in RAM."""
        broken[KEY] = "x"
        assert broken.connection.is_open
        assert broken.ram[KEY] == "x"
        assert broken[KEY] == "x"

    def test_delete_error(self, broken):
        """A Redis error on delete is swallowed and opens the breaker."""
        del broken[KEY]
        assert broken.connection.is_open
        assert counters(broken)["errors"] == 1

    def test_breaker_skips_redis(self, broken, failing, clock):
        """While the breaker is open, Redis is not called at all."""
        broken[KEY] = "x"
        assert failing.calls == ["set"]
        for _ in range(10):
            broken[KEY] = "y"
            assert broken[KEY] == "y"
            del broken[KEY]
        assert failing.calls == ["set"]
        clock.advance(30)
        broken.get(KEY)
        assert failing.calls == ["set", "get"]

    def test_recovery(self, make_adapter, settings, server, clock, inspector):
        """After ``retry_after``, a working Redis is used again."""
        import fakeredis

        state = {"down": True}

        def factory(s):
            if state["down"]:
                return FailingClient(redis.ConnectionError("down"))
            return fakeredis.FakeRedis(server=server)

        connection = Connection(settings, factory=factory, clock=clock)
        adapter = make_adapter(connection=connection)
        adapter[KEY] = "during outage"
        assert inspector.keys("*") == []
        state["down"] = False
        connection._client = None
        clock.advance(30)
        adapter[KEY] = "after outage"
        assert connection.is_open is False
        assert inspector.get(adapter.redis_key(KEY)) is not None

    def test_undecodable_payload_is_a_miss(self, adapter, inspector):
        """A payload this code cannot decode is a miss, without opening the breaker."""
        inspector.set(adapter.redis_key(KEY), b"\x09garbage")
        with pytest.raises(KeyError):
            adapter[KEY]
        assert adapter.connection.is_open is False
        assert counters(adapter)["undecodable"] == 1

    def test_ram_hit_while_open(self, broken):
        """A value stored in RAM during an outage is a RAM hit."""
        broken[KEY] = "x"
        assert broken[KEY] == "x"
        assert counters(broken)["ram_hits"] == 1
