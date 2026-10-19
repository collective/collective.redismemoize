(concepts-cache-routes)=

# Which Plone caches land where

<!-- source: tests/spikes/__init__.py (PLONE_RAM_CACHES), tests/spikes/test_spike_ram_cache_users.py, tests/integration/test_plone_caches.py, tests/integration/test_plone_app_caching.py -->

A stock Plone 6.2 has ten functions decorated with `plone.memoize.ram`, plus the RAM page cache of `plone.app.caching`.
The test suite scans the installed Plone for them, so a release that adds, removes, or renames one fails a test and this table gets updated.

The **Evidence** column says how each route is known.
*Tested* means a test calls the real function on a Plone site and checks where the value went.
*Return type* means the route follows from what the function returns, read from its source, without a test that drives it.

| Function | Returns | Route | Evidence |
|---|---|---|---|
| `plone.app.caching.operations.ramcache` (page cache) | status, headers, body, and a flag | `redis` | Tested |
| `plone.app.content.browser.i18n._gettext_catalog` | a dictionary of translations | `redis` | Tested |
| `plone.app.layout.sitemap.sitemap.generate` | the sitemap compressed with gzip, as bytes | `redis` | Tested |
| `plone.app.theming.plugins.utils.getPluginSettings` | dictionaries of strings | `redis` | Tested |
| `plone.app.theming.plugins.utils.getPlugins` | name and plugin pairs | `redis` on a stock site, `ram-not-shareable` with any theme plugin | Tested, both cases |
| `plone.app.event.portlets.portlet_events.events` | event accessor objects | `ram-not-shareable` | Return type |
| `plone.app.layout.links.viewlets.render` | HTML, as a string | `redis` | Return type |
| `plone.app.multilingual.browser.viewlets.get_alternate_languages` | a list of dictionaries of strings | `redis` | Return type |
| `plone.app.portlets.portlets.news.render` | HTML, as a string | `redis` | Return type |
| `plone.namedfile.scaling.tag` | an image tag, as a string | `redis` | Return type |
| `plone.app.portlets.portlets.recent.render` | never cached | none | Source |

Two rows deserve a comment.

`getPlugins` returns the registered theme plugins as `(name, plugin)` pairs.
A stock Plone registers none, so the list is empty, which is plain data, and it is shared.
As soon as an add-on registers a theme plugin, the list holds a utility, the function is routed to RAM, and the log names the plugin's class.
Both cases are tested.

The recent items portlet calls `ram.cache(...)` on a line of its own instead of using it as a decorator, so its `render` method is never cached, in stock Plone or with this package.

## Related

- {doc}`what-shareable-means`
- {doc}`per-function-routing`
- {doc}`/how-to-guides/include-and-exclude-functions`
