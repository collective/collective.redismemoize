"""The ``ICacheChooser`` utility, as Plone sees it."""

from . import COMPUTE
from collective.redismemoize.adapter import RedisCacheAdapter
from collective.redismemoize.chooser import choose_cache
from plone.memoize import ram
from plone.memoize.interfaces import ICacheChooser
from zope.component import queryUtility
from zope.ramcache.interfaces.ram import IRAMCache


class TestRegistration:
    def test_ours_is_registered(self):
        """The registered chooser is this package's, not plone.memoize's."""
        assert queryUtility(ICacheChooser) is choose_cache

    def test_provides_interface(self):
        """The chooser provides ``ICacheChooser``."""
        assert ICacheChooser.providedBy(choose_cache)


class TestInactive:
    def test_same_as_stock(self):
        """Unconfigured, the answer is exactly plone.memoize's."""
        ours = choose_cache(COMPUTE)
        stock = ram.choose_cache(COMPUTE)
        assert type(ours) is type(stock) is ram.RAMCacheAdapter
        assert ours.globalkey == stock.globalkey == COMPUTE
        assert ours.ramcache is stock.ramcache is queryUtility(IRAMCache)

    def test_same_storage(self):
        """A value stored through ours is read through the stock adapter."""
        choose_cache(COMPUTE)["key"] = "value"
        assert ram.choose_cache(COMPUTE)["key"] == "value"

    def test_nothing_recorded(self, routes):
        """Inert means no bookkeeping either."""
        choose_cache(COMPUTE)
        assert routes() == {}


class TestActive:
    def test_redis_adapter(self, redis_server):
        """Configured, a function gets a Redis adapter over the stock RAM cache."""
        adapter = choose_cache(COMPUTE)
        assert isinstance(adapter, RedisCacheAdapter)
        assert adapter.globalkey == COMPUTE
        assert adapter.ram.ramcache is queryUtility(IRAMCache)
        assert adapter.ram.globalkey == COMPUTE

    def test_excluded(self, activate, routes):
        """An excluded function gets the stock RAM adapter, and it is recorded."""
        activate(REDIS_MEMOIZE_EXCLUDE="tests.integration.*")
        adapter = choose_cache(COMPUTE)
        assert type(adapter) is ram.RAMCacheAdapter
        assert routes()[COMPUTE]["route"] == "ram-excluded"

    def test_not_included(self, activate, routes):
        """A function outside the include list stays in RAM."""
        activate(REDIS_MEMOIZE_INCLUDE="plone.*")
        assert type(choose_cache(COMPUTE)) is ram.RAMCacheAdapter
        assert "INCLUDE" in routes()[COMPUTE]["reason"]

    def test_included(self, activate):
        """A function in the include list goes to Redis."""
        activate(REDIS_MEMOIZE_INCLUDE="tests.*")
        assert isinstance(choose_cache(COMPUTE), RedisCacheAdapter)
