"""Spikes: how Plone and plone.memoize behave, pinned as regression tests.

Each module asserts something this package's design relies on, and none of
them routes through the package's own adapter or serializer. A spike failing
means upstream changed, not that our code broke.
"""

from pathlib import Path


#: The script that loads ZCML the way a real Zope startup does.
STARTUP_SCRIPT = Path(__file__).parent / "startup.py"

#: The stock chooser, by dotted name.
STOCK_CHOOSER = "plone.memoize.ram.choose_cache"

#: Ours, by dotted name.
OUR_CHOOSER = "collective.redismemoize.chooser.choose_cache"

#: Every ``plone.memoize.ram`` cache in a stock Plone 6.2, and where its values
#: land once this package is active. ``None`` means the decorator is written
#: without ``@`` and so caches nothing. ``getPlugins`` returns an empty list on
#: a stock site, which registers no ``IThemePlugin``; with any plugin
#: registered it holds utilities and goes to RAM. The routes are asserted by
#: ``tests/integration/test_plone_caches.py`` where they can be driven cheaply,
#: and the list itself by ``test_spike_ram_cache_users``.
PLONE_RAM_CACHES = {
    "plone.app.content.browser.i18n._gettext_catalog": "redis",
    "plone.app.event.portlets.portlet_events.events": "ram-not-shareable",
    "plone.app.layout.links.viewlets.render": "redis",
    "plone.app.layout.sitemap.sitemap.generate": "redis",
    "plone.app.multilingual.browser.viewlets.get_alternate_languages": "redis",
    "plone.app.portlets.portlets.news.render": "redis",
    "plone.app.portlets.portlets.recent.render": None,
    "plone.app.theming.plugins.utils.getPluginSettings": "redis",
    "plone.app.theming.plugins.utils.getPlugins": "redis",
    "plone.namedfile.scaling.tag": "redis",
}
