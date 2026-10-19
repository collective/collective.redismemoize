"""Plone's own RAM caches, driven for real, and where they land.

Only the ones that can be driven cheaply in an integration test are here. The
full table, including the ones documented from their return type, is
``tests.spikes.PLONE_RAM_CACHES``.
"""

from plone import api
from plone.app.testing import logout
from tests.spikes import PLONE_RAM_CACHES

import gzip
import pytest


I18N = "plone.app.content.browser.i18n._gettext_catalog"
PLUGINS = "plone.app.theming.plugins.utils.getPlugins"
PLUGIN_SETTINGS = "plone.app.theming.plugins.utils.getPluginSettings"
SITEMAP = "plone.app.layout.sitemap.sitemap.generate"


def stored(client, fun_name: str) -> int:
    """Count the Redis keys of one function."""
    return len(client.keys(f"test.memoize:{fun_name}:*"))


@pytest.fixture
def theme_directory(portal):
    """Return the resource directory of the Barceloneta theme."""
    from plone.resource.utils import queryResourceDirectory

    return queryResourceDirectory("theme", "barceloneta")


class TestShared:
    def test_i18n_catalog(self, portal, redis_client, routes):
        """The JavaScript i18n catalog is a dict of strings: shared."""
        view = api.content.get_view("plonejsi18n", portal, portal.REQUEST)
        catalog = view._gettext_catalog("plone", "en")
        assert view._gettext_catalog("plone", "en") == catalog
        assert routes()[I18N]["route"] == PLONE_RAM_CACHES[I18N] == "redis"
        assert stored(redis_client, I18N) == 1
        assert routes()[I18N]["counters"]["redis_hits"] == 1

    def test_theme_plugin_settings(self, theme_directory, redis_client, routes):
        """Theme plugin settings are dicts of strings: shared."""
        from plone.app.theming.plugins.utils import getPluginSettings

        getPluginSettings(theme_directory, [])
        assert routes()[PLUGIN_SETTINGS]["route"] == PLONE_RAM_CACHES[PLUGIN_SETTINGS]
        assert stored(redis_client, PLUGIN_SETTINGS) == 1

    def test_sitemap(self, portal, redis_client, routes):
        """The gzipped sitemap is bytes: shared."""
        view = api.content.get_view("sitemap.xml.gz", portal, portal.REQUEST)
        logout()
        body = view.generate()
        assert gzip.decompress(body).startswith(b"<?xml")
        assert view.generate() == body
        assert routes()[SITEMAP]["route"] == PLONE_RAM_CACHES[SITEMAP] == "redis"
        assert stored(redis_client, SITEMAP) == 1

    def test_theme_plugins_on_a_stock_site(self, portal, redis_client, routes):
        """A stock site registers no theme plugin: the empty list is shared."""
        from plone.app.theming.plugins.utils import getPlugins

        assert getPlugins() == []
        assert routes()[PLUGINS]["route"] == PLONE_RAM_CACHES[PLUGINS] == "redis"
        assert stored(redis_client, PLUGINS) == 1


class ThemePlugin:
    """A theme plugin, as an add-on would register one."""

    dependencies = ()


@pytest.fixture
def theme_plugin():
    """Register a theme plugin utility for one test."""
    from plone.app.theming.interfaces import IThemePlugin
    from zope.component import getGlobalSiteManager

    plugin = ThemePlugin()
    gsm = getGlobalSiteManager()
    gsm.registerUtility(plugin, IThemePlugin, name="example")
    yield plugin
    gsm.unregisterUtility(plugin, IThemePlugin, name="example")


class TestKeptInRam:
    def test_theme_plugins(self, portal, theme_plugin, redis_client, routes):
        """With a plugin registered, the list holds a utility: kept in RAM."""
        from plone.app.theming.plugins.utils import getPlugins

        plugins = getPlugins()
        assert plugins == [("example", theme_plugin)]
        assert getPlugins()[0][1] is theme_plugin
        route = routes()[PLUGINS]
        assert route["route"] == "ram-not-shareable"
        assert route["reason"] == (
            "value[0][1] is a tests.integration.test_plone_caches.ThemePlugin"
        )
        assert stored(redis_client, PLUGINS) == 0
        assert route["counters"]["ram_hits"] == 1
