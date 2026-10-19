"""A ``@ram.cache`` function, end to end, through this package."""

from . import CALLS
from . import COMPUTE
from . import compute
from . import COMPUTE_OTHER
from . import compute_other
from . import never_cached
from collective.redismemoize import testing
from plone.memoize import ram


def redis_keys(client, fun_name: str) -> list[bytes]:
    """Return the Redis keys of one function."""
    return client.keys(f"test.memoize:{fun_name}:*")


class TestThroughRedis:
    def test_miss_compute_hit(self, redis_client):
        """The first call computes and stores; the second is served from Redis."""
        assert compute("en") == {"lang": "en", "region": "BR"}
        assert compute("en") == {"lang": "en", "region": "BR"}
        assert CALLS == [("compute", "en", "BR")]
        assert len(redis_keys(redis_client, COMPUTE)) == 1

    def test_hit_is_a_copy(self, redis_server):
        """Mutating a returned value does not change what the next call gets."""
        compute("en")["lang"] = "changed"
        assert compute("en")["lang"] == "en"

    def test_positional_and_keyword_keys(self, redis_client):
        """Keys are built from the arguments as the key function returns them."""
        compute("en", "PT")
        compute("en", region="PT")
        compute("en", region="BR")
        assert CALLS == [("compute", "en", "PT"), ("compute", "en", "BR")]
        assert len(redis_keys(redis_client, COMPUTE)) == 2

    def test_functions_do_not_collide(self, redis_client):
        """Two functions with the same key get two values."""
        assert compute("en") != compute_other("en")
        assert len(redis_keys(redis_client, COMPUTE)) == 1
        assert len(redis_keys(redis_client, COMPUTE_OTHER)) == 1

    def test_dont_cache(self, redis_client):
        """``DontCache`` skips the cache entirely."""
        never_cached("en")
        never_cached("en")
        assert len(CALLS) == 2
        assert redis_client.keys("*") == []

    def test_global_cache_invalidation_leaves_redis(self, redis_client):
        """``global_cache.invalidateAll()``, which plone.app.testing calls, leaves Redis.

        Values survive in Redis between plone.app.testing tests unless
        something flushes them, which is what ``testing.clean`` is for.
        """
        compute("en")
        ram.global_cache.invalidateAll()
        compute("en")
        assert len(CALLS) == 1
        testing.clean()
        compute("en")
        assert len(CALLS) == 2

    def test_counters(self, redis_server, routes):
        """The routing table counts the miss and the hit."""
        compute("en")
        compute("en")
        counters = routes()[COMPUTE]["counters"]
        assert counters["redis_misses"] == 1
        assert counters["redis_hits"] == 1


class TestInactive:
    def test_still_caches_in_ram(self):
        """Unconfigured, caching works exactly as before, in RAM."""
        compute("en")
        compute("en")
        assert CALLS == [("compute", "en", "BR")]
