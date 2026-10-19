"""Where each cached function's values live, and what happened to them.

Routing is decided per function, for the lifetime of the process. A function
whose value was refused once is kept in RAM from then on: the next call does
not pay for another serialization attempt and a Redis round-trip only to be
refused again. Size is the exception and is decided per value, because the
size of a value varies from call to call while its type rarely does.

The counters are what an operator reads to make the one judgement this
package cannot make: a value can be plain data and still be wrong to share,
when its cache key leaves out something that differs between instances.

This module is pure Python and never imports Zope.
"""

from collections import Counter
from collective.redismemoize import logger

import enum
import threading


class Route(enum.Enum):
    """Where a function's values are stored."""

    #: Shared, in Redis. The default for every function not routed elsewhere.
    REDIS = "redis"
    #: In the RAM cache, because the configuration excludes the function.
    RAM_EXCLUDED = "ram-excluded"
    #: In the RAM cache, because one of its values was not plain data.
    RAM_NOT_SHAREABLE = "ram-not-shareable"


#: The counters kept per function, in the order they are reported.
COUNTERS = (
    "redis_hits",
    "redis_misses",
    "ram_hits",
    "ram_misses",
    "refused",
    "too_large",
    "undecodable",
    "errors",
)


class Router:
    """Per-process routes and counters, safe to use from several threads."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._routes: dict[str, Route] = {}
        self._reasons: dict[str, str] = {}
        self._counters: dict[str, Counter[str]] = {}

    def route_for(self, fun_name: str) -> Route:
        """Return the route of a function.

        :param fun_name: Dotted name of the cached function.
        :returns: The learned route, or :attr:`Route.REDIS`.
        """
        return self._routes.get(fun_name, Route.REDIS)

    def learn(self, fun_name: str, route: Route, reason: str) -> bool:
        """Route a function to RAM for the rest of the process.

        The first route learned for a function wins; it is logged once.

        :param fun_name: Dotted name of the cached function.
        :param route: Where its values go from now on.
        :param reason: Why, for the log and for :meth:`snapshot`.
        :returns: Whether this call changed the route.
        """
        with self._lock:
            if fun_name in self._routes:
                return False
            self._routes[fun_name] = route
            self._reasons[fun_name] = reason
        logger.info("%s: values kept in RAM (%s): %s", fun_name, route.value, reason)
        return True

    def count(self, fun_name: str, counter: str) -> None:
        """Add one to a counter.

        :param fun_name: Dotted name of the cached function.
        :param counter: One of :data:`COUNTERS`.
        :raises ValueError: For a counter that does not exist.
        """
        if counter not in COUNTERS:
            raise ValueError(f"unknown counter {counter!r}")
        with self._lock:
            self._counters.setdefault(fun_name, Counter())[counter] += 1

    def snapshot(self) -> dict[str, dict]:
        """Return every function seen, its route and its counters.

        :returns: ``{fun_name: {"route", "reason", "counters"}}``, sorted.
        """
        with self._lock:
            names = sorted(set(self._routes) | set(self._counters))
            return {
                name: {
                    "route": self._routes.get(name, Route.REDIS).value,
                    "reason": self._reasons.get(name),
                    "counters": {
                        counter: self._counters.get(name, Counter())[counter]
                        for counter in COUNTERS
                    },
                }
                for name in names
            }

    def reset(self) -> None:
        """Forget every route and counter."""
        with self._lock:
            self._routes.clear()
            self._reasons.clear()
            self._counters.clear()


#: The process router.
router = Router()
