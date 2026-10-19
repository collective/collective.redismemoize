"""The test layer and helpers offered to add-on authors."""

from collective.redismemoize import config
from collective.redismemoize import testing
from collective.redismemoize.adapter import RedisCacheAdapter
from collective.redismemoize.chooser import choose_cache
from collective.redismemoize.routing import router
from plone.memoize.interfaces import ICacheChooser
from plone.memoize.ram import choose_cache as stock_chooser
from plone.testing import zca
from zope.component import getGlobalSiteManager
from zope.component import provideUtility
from zope.component import queryUtility

import os
import pytest


@pytest.fixture
def layer():
    """Set up :data:`REDIS_MEMOIZE_FIXTURE` on its base, and tear both down."""
    zca.ZCML_DIRECTIVES.setUp()
    layer = testing.RedisMemoizeLayer()
    layer.setUp()
    yield layer
    layer.tearDown()
    zca.ZCML_DIRECTIVES.tearDown()


class TestLayer:
    def test_registers_chooser(self, layer):
        """Within the layer, the chooser is ours, without the package ZCML."""
        assert queryUtility(ICacheChooser) is choose_cache

    def test_active(self, layer):
        """Within the layer, functions get a Redis adapter."""
        assert config.get_settings().active is True
        assert isinstance(choose_cache("a.b"), RedisCacheAdapter)

    def test_test_setup_cleans(self, layer):
        """``testSetUp`` empties the fake server and forgets routes."""
        adapter = choose_cache("a.b")
        adapter["k"] = "v"
        router.count("a.b", "ram_hits")
        layer.testSetUp()
        assert router.snapshot() == {}
        assert adapter.get("k") is None

    def test_chooser_survives_a_layer_on_top(self, layer):
        """A registry stacked later with the stock chooser does not hide ours."""
        zca.pushGlobalRegistry()
        try:
            provideUtility(stock_chooser, ICacheChooser)
            layer.testSetUp()
            assert queryUtility(ICacheChooser) is choose_cache
            layer.testTearDown()
            assert queryUtility(ICacheChooser) is stock_chooser
        finally:
            zca.popGlobalRegistry()

    def test_chooser_replaced_below(self, layer):
        """A registry below ours, as a Plone site's base, gets our chooser too.

        A site's own registry is based on a registry below the one this layer
        stacks, so that one must answer with our chooser during the test.
        """
        (below,) = getGlobalSiteManager().__bases__
        below.registerUtility(stock_chooser, ICacheChooser)
        try:
            layer.testSetUp()
            assert below.getUtility(ICacheChooser) is choose_cache
            layer.testTearDown()
            assert below.getUtility(ICacheChooser) is stock_chooser
        finally:
            below.unregisterUtility(provided=ICacheChooser)

    def test_our_chooser_is_left_alone(self, layer):
        """When every chooser is already ours, nothing is replaced or restored."""
        layer.testSetUp()
        assert layer._replaced_choosers == []
        layer.testTearDown()
        assert queryUtility(ICacheChooser) is choose_cache

    def test_tear_down_restores(self):
        """After the layer, the chooser and the environment are as before."""
        before = queryUtility(ICacheChooser)
        url = os.environ.get("REDIS_MEMOIZE_URL")
        zca.ZCML_DIRECTIVES.setUp()
        layer = testing.RedisMemoizeLayer()
        layer.setUp()
        layer.tearDown()
        zca.ZCML_DIRECTIVES.tearDown()
        assert queryUtility(ICacheChooser) is before
        assert os.environ.get("REDIS_MEMOIZE_URL") == url
        assert config.get_settings().active is (url is not None)


class TestHelpers:
    def test_activate_and_deactivate(self, monkeypatch):
        """``activate`` sets the variables; ``deactivate`` restores them."""
        monkeypatch.setenv("REDIS_MEMOIZE_TTL", "77")
        server = testing.activate(REDIS_MEMOIZE_TTL="5")
        assert server is not None
        assert config.get_settings().ttl == 5
        assert config.get_settings().prefix == "test.memoize"
        testing.deactivate()
        assert os.environ["REDIS_MEMOIZE_TTL"] == "77"
        assert "REDIS_MEMOIZE_URL" not in os.environ
        assert config.get_settings().active is False

    def test_activate_twice_keeps_first_snapshot(self, monkeypatch):
        """Activating twice still restores the environment from before the first."""
        monkeypatch.delenv("REDIS_MEMOIZE_TTL", raising=False)
        testing.activate()
        testing.activate(REDIS_MEMOIZE_TTL="9")
        testing.deactivate()
        assert "REDIS_MEMOIZE_TTL" not in os.environ

    def test_activate_with_server(self):
        """A given server is used, so two activations can share one."""
        import fakeredis

        server = fakeredis.FakeServer()
        assert testing.activate(server) is server
        testing.deactivate()

    def test_deactivate_without_activate(self):
        """``deactivate`` alone is harmless."""
        testing.deactivate()
        assert config.get_settings().active is False
