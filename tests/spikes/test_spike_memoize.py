"""The plone.memoize contract this package plugs into."""

from plone.memoize import ram
from plone.memoize import volatile
from plone.memoize.interfaces import ICacheChooser
from zope.component import getGlobalSiteManager

import inspect
import pytest


class RecordingCache(dict):
    """A dict that records the keys it is asked for."""

    def __init__(self):
        super().__init__()
        self.asked: list[str] = []

    def get(self, key, default=None):
        self.asked.append(key)
        return super().get(key, default)


def compute(lang, *, region="BR"):
    return f"{lang}-{region}"


def test_volatile_key_format():
    """``volatile.cache`` prefixes the key with the dotted function name."""
    cache = RecordingCache()
    cached = volatile.cache(
        lambda fun, *a, **kw: (a, kw), get_cache=lambda *a, **kw: cache
    )(compute)
    assert cached("pt", region="PT") == "pt-PT"
    assert cache.asked == [f"{__name__}.compute:(('pt',), {{'region': 'PT'}})"]


def test_volatile_uses_get_and_setitem():
    """The adapter contract: ``get(key, marker)``, then ``__setitem__``."""
    source = inspect.getsource(volatile.cache)
    assert "cache.get(key, _marker)" in source
    assert "cache[key] = fun(*args, **kwargs)" in source


def test_dont_cache():
    """``DontCache`` from the key function skips the cache entirely."""
    cache = RecordingCache()

    def key(fun, *args):
        raise volatile.DontCache

    cached = volatile.cache(key, get_cache=lambda *a, **kw: cache)(compute)
    assert cached("en") == "en-BR"
    assert cache.asked == []


def test_store_in_cache_asks_the_chooser():
    """``ram.store_in_cache`` asks the ``ICacheChooser`` utility, by dotted name."""
    asked: list[str] = []

    def chooser(fun_name):
        asked.append(fun_name)
        return {}

    gsm = getGlobalSiteManager()
    gsm.registerUtility(chooser, ICacheChooser)
    try:
        ram.store_in_cache(compute)
    finally:
        gsm.unregisterUtility(chooser, ICacheChooser)
    assert asked == [f"{__name__}.compute"]


def test_store_in_cache_without_chooser():
    """Without any chooser, ``store_in_cache`` falls back to ``global_cache``."""
    adapter = ram.store_in_cache(compute)
    assert isinstance(adapter, ram.RAMCacheAdapter)
    assert adapter.ramcache is ram.global_cache


def test_stock_chooser():
    """The stock chooser wraps the ``IRAMCache`` utility, keyed by function."""
    source = inspect.getsource(ram.choose_cache)
    assert (
        "RAMCacheAdapter(component.queryUtility(IRAMCache), globalkey=fun_name)"
        in source
    )


def test_global_cache_max_age():
    """``global_cache`` keeps values a day, the default TTL this package uses."""
    assert ram.global_cache.maxAge == 86400


@pytest.mark.parametrize("name", ["get", "__getitem__", "__setitem__"])
def test_memcache_adapter_shape(name: str):
    """plone.memoize's own MemcacheAdapter has the same three methods."""
    assert hasattr(ram.MemcacheAdapter, name)


def test_ram_adapter_has_no_delitem():
    """The stock adapter cannot delete; ours goes to the RAM cache directly."""
    assert not hasattr(ram.RAMCacheAdapter, "__delitem__")


def test_plone_app_testing_clears_global_cache():
    """plone.app.testing clears ``global_cache`` between tests, and nothing else."""
    from plone.app.testing import layers
    from plone.app.testing.layers import PloneFixture  # noqa: F401

    source = inspect.getsource(layers)
    assert "global_cache.invalidateAll()" in source
    assert "redis" not in source.lower()
