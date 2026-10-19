"""The public API: invalidation, status and the TTL decorator."""

from . import CALLS
from . import COMPUTE
from . import compute
from . import COMPUTE_OTHER
from . import compute_other
from collective.redismemoize import api
from collective.redismemoize.client import get_connection
from plone.memoize import ram
from zope.component import queryUtility
from zope.ramcache.interfaces.ram import IRAMCache

import pytest
import redis


TTL_FUN = f"{__name__}.short_lived"


def _key(fun, lang):
    return lang


@api.cache(_key, ttl=60)
def short_lived(lang):
    """A function cached for one minute."""
    CALLS.append(("short_lived", lang))
    return lang


@api.cache(_key)
def default_lived(lang):
    """A function cached for the default TTL."""
    CALLS.append(("default_lived", lang))
    return lang


class FailingClient:
    """Fails every command."""

    def __getattr__(self, name):
        def fail(*args, **kwargs):
            raise redis.ConnectionError("down")

        return fail


class TestRamCaches:
    def test_both_caches(self):
        """The layer's IRAMCache utility and global_cache are both returned."""
        caches = api.ram_caches()
        assert caches[0] is ram.global_cache
        assert queryUtility(IRAMCache) in caches

    def test_same_cache_once(self, monkeypatch):
        """When the utility is global_cache, it is returned once."""
        monkeypatch.setattr(api, "queryUtility", lambda iface: ram.global_cache)
        assert api.ram_caches() == [ram.global_cache]

    def test_no_utility(self, monkeypatch):
        """Without any utility, only global_cache."""
        monkeypatch.setattr(api, "queryUtility", lambda iface: None)
        assert api.ram_caches() == [ram.global_cache]


class TestInvalidate:
    def test_one_function(self, redis_client):
        """``invalidate`` drops one function's values and leaves the others."""
        compute("en")
        compute_other("en")
        assert api.invalidate(COMPUTE) == 1
        assert redis_client.keys(f"test.memoize:{COMPUTE}:*") == []
        assert len(redis_client.keys(f"test.memoize:{COMPUTE_OTHER}:*")) == 1
        compute("en")
        compute_other("en")
        assert [c[0] for c in CALLS] == ["compute", "compute_other", "compute"]

    def test_also_drops_ram(self, redis_server):
        """Values kept in RAM are dropped too."""
        for cache in api.ram_caches():
            ram.RAMCacheAdapter(cache, globalkey=COMPUTE)["k"] = "v"
        api.invalidate(COMPUTE)
        for cache in api.ram_caches():
            assert ram.RAMCacheAdapter(cache, globalkey=COMPUTE).get("k") is None

    def test_glob_characters_are_literal(self, redis_client):
        """A function name with glob characters matches only itself."""
        redis_client.set("test.memoize:a.b:1", b"x")
        redis_client.set("test.memoize:a*:1", b"x")
        assert api.invalidate("a*") == 1
        assert redis_client.keys("*") == [b"test.memoize:a.b:1"]

    def test_batches(self, redis_client, monkeypatch):
        """More keys than one batch are all removed."""
        monkeypatch.setattr(api, "BATCH_SIZE", 3)
        for index in range(10):
            redis_client.set(f"test.memoize:{COMPUTE}:{index}", b"x")
        assert api.invalidate(COMPUTE) == 10
        assert redis_client.keys("*") == []

    def test_inactive(self):
        """Unconfigured, only RAM is dropped and nothing is counted."""
        compute("en")
        assert api.invalidate(COMPUTE) == 0
        compute("en")
        assert len(CALLS) == 2

    def test_redis_down(self, redis_server, monkeypatch):
        """With Redis down, invalidation drops RAM, reports 0 and opens the breaker."""
        from collective.redismemoize import client

        client.set_factory(lambda s: FailingClient())
        assert api.invalidate(COMPUTE) == 0
        assert get_connection().is_open


class TestInvalidateAll:
    def test_everything_under_the_prefix(self, redis_client):
        """``invalidate_all`` drops the prefix and nothing outside it."""
        compute("en")
        compute_other("en")
        redis_client.set("other.prefix:x", b"keep")
        assert api.invalidate_all() == 2
        assert redis_client.keys("*") == [b"other.prefix:x"]

    def test_prefix_is_literal(self, activate):
        """A prefix with glob characters matches only itself."""
        import fakeredis

        client = fakeredis.FakeRedis(server=activate(REDIS_MEMOIZE_PREFIX="p[1]"))
        client.set("p[1]:a:1", b"x")
        client.set("p1:a:1", b"x")
        assert api.invalidate_all() == 1
        assert client.keys("*") == [b"p1:a:1"]

    def test_inactive(self):
        """Unconfigured, only RAM is dropped."""
        assert api.invalidate_all() == 0


class TestStatus:
    def test_inactive(self):
        """Unconfigured: settings, and nothing about a server."""
        status = api.status()
        assert status["active"] is False
        assert status["server"] is None
        assert status["breaker"] is None
        assert status["settings"]["url"] is None
        assert status["functions"] == {}

    def test_active(self, redis_server):
        """Configured: the server answers and the breaker is closed."""
        compute("en")
        status = api.status()
        assert status["active"] is True
        assert status["settings"] == {
            "url": "redis://fakeredis:6379/0",
            "prefix": "test.memoize",
            "ttl": 86400,
            "timeout": 0.25,
            "retry_after": 30.0,
            "max_size": 1048576,
            "include": [],
            "exclude": [],
        }
        assert status["breaker"] == {"open": False, "seconds_until_retry": 0.0}
        assert status["server"]["product"] == "redis"
        # fakeredis does not implement INFO; the docker tests check a version.
        assert status["server"]["version"] is None
        assert status["server"]["latency_ms"] >= 0
        assert status["server"]["error"] is None
        assert status["functions"][COMPUTE]["counters"]["redis_misses"] == 1

    def test_password_redacted(self, activate):
        """The URL's password never appears."""
        activate(REDIS_MEMOIZE_URL="redis://:s3cret@cache:6379/0")
        status = api.status()
        assert status["settings"]["url"] == "redis://:***@cache:6379/0"
        assert "s3cret" not in repr(status)

    def test_valkey(self, redis_server, monkeypatch):
        """A Valkey server is reported as such."""
        from collective.redismemoize import client

        class Valkey:
            def ping(self):
                return True

            def info(self, section):
                return {"valkey_version": "8.1.1", "redis_version": "7.2.4"}

        client.set_factory(lambda s: Valkey())
        server = api.status()["server"]
        assert server["product"] == "valkey"
        assert server["version"] == "8.1.1"

    def test_no_version(self, redis_server):
        """A server that reports no version is reported as unknown."""
        from collective.redismemoize import client

        class Quiet:
            def ping(self):
                return True

            def info(self, section):
                return {}

        client.set_factory(lambda s: Quiet())
        assert api.status()["server"]["version"] is None

    def test_redis_down(self, redis_server):
        """With Redis down: the error is reported and the breaker opens."""
        from collective.redismemoize import client

        client.set_factory(lambda s: FailingClient())
        status = api.status()
        assert status["server"]["error"] == "ConnectionError: down"
        assert status["server"]["latency_ms"] is None
        assert status["breaker"]["open"] is True
        assert status["breaker"]["seconds_until_retry"] == pytest.approx(30, abs=1)


class TestCacheDecorator:
    def test_ttl(self, redis_client):
        """``api.cache(..., ttl=60)`` stores with that TTL."""
        assert short_lived("en") == "en"
        assert short_lived("en") == "en"
        assert CALLS == [("short_lived", "en")]
        (key,) = redis_client.keys(f"test.memoize:{TTL_FUN}:*")
        assert 55 <= redis_client.ttl(key) <= 60

    def test_default_ttl(self, redis_client):
        """Without ``ttl``, the configured default applies."""
        default_lived("en")
        (key,) = redis_client.keys("test.memoize:*default_lived:*")
        assert redis_client.ttl(key) > 86000

    def test_inactive(self):
        """Unconfigured, it caches in RAM like ``ram.cache``."""
        short_lived("en")
        short_lived("en")
        assert CALLS == [("short_lived", "en")]

    @pytest.mark.parametrize("ttl", [0, -1, 1.5, "60", True])
    def test_invalid_ttl(self, ttl):
        """A TTL that is not a positive integer is refused at decoration."""
        with pytest.raises(ValueError, match="ttl"):
            api.cache(_key, ttl=ttl)
