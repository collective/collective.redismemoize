"""The ``ICacheChooser`` utility this package registers.

``plone.memoize.ram.cache`` and ``plone.app.caching``'s RAM page cache both
ask the ``ICacheChooser`` utility for a mapping per function. Stock Plone
answers with a ``RAMCacheAdapter`` over the process-local ``global_cache``;
:func:`choose_cache` answers the same, except for a configured function that
may use Redis.

The settings are read when this module is imported, which happens while the
ZCML loads: an invalid variable stops the process at startup, not at the
first request.
"""

from collective.redismemoize.adapter import RedisCacheAdapter
from collective.redismemoize.client import get_connection
from collective.redismemoize.config import get_settings
from collective.redismemoize.routing import Route
from collective.redismemoize.routing import router
from plone.memoize.interfaces import ICacheChooser
from plone.memoize.ram import AbstractDict
from plone.memoize.ram import RAMCacheAdapter
from zope.component import queryUtility
from zope.interface import directlyProvides
from zope.ramcache.interfaces.ram import IRAMCache


get_settings()


def choose_cache(fun_name: str) -> AbstractDict:
    """Return the cache for one function.

    :param fun_name: Dotted name of the cached function.
    :returns: The stock RAM adapter when the package is not configured or the
        function is excluded; a :class:`RedisCacheAdapter` otherwise.
    """
    ram = RAMCacheAdapter(queryUtility(IRAMCache), globalkey=fun_name)
    settings = get_settings()
    if not settings.active:
        return ram
    reason = settings.exclusion_reason(fun_name)
    if reason is not None:
        router.learn(fun_name, Route.RAM_EXCLUDED, reason)
        return ram
    return RedisCacheAdapter(fun_name, settings, ram, router, get_connection())


directlyProvides(choose_cache, ICacheChooser)
