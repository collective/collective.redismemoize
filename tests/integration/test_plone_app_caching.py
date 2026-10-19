"""plone.app.caching's RAM page cache goes through the same chooser."""

from collective.redismemoize.adapter import RedisCacheAdapter
from plone.app.caching.operations import utils
from plone.memoize.ram import RAMCacheAdapter


class TestGetRAMCache:
    def test_inactive(self):
        """Unconfigured, the page cache is the stock RAM adapter."""
        assert type(utils.getRAMCache()) is RAMCacheAdapter

    def test_active(self, redis_server):
        """Configured, the page cache is a Redis adapter for its global key."""
        cache = utils.getRAMCache()
        assert isinstance(cache, RedisCacheAdapter)
        assert cache.globalkey == utils.PAGE_CACHE_KEY


class TestRoundTrip:
    def test_store_and_fetch(self, portal, http_request, redis_client, routes):
        """A response stored by plone.app.caching is plain data: it goes to Redis."""
        response = http_request.response
        response.setHeader("Content-Type", "text/html; charset=utf-8")
        utils.cacheInRAM(portal, http_request, response, etag="|abc")
        utils.storeResponseInRAMCache(http_request, response, b"<html>page</html>")

        assert len(redis_client.keys(f"test.memoize:{utils.PAGE_CACHE_KEY}:*")) == 1
        status, headers, body, gzip_flag = utils.fetchFromRAMCache(
            http_request, etag="|abc"
        )
        assert status == 200
        assert headers["content-type"] == "text/html; charset=utf-8"
        assert body == b"<html>page</html>"
        assert gzip_flag in (True, False)
        assert routes()[utils.PAGE_CACHE_KEY]["route"] == "redis"
        assert routes()[utils.PAGE_CACHE_KEY]["counters"]["redis_hits"] == 1
