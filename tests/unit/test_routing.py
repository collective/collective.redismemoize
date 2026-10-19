"""Per-function routes and counters."""

from collective.redismemoize.routing import COUNTERS
from collective.redismemoize.routing import Route
from collective.redismemoize.routing import Router
from tests import FUN_NAME

import logging
import pytest
import threading


class TestRoutes:
    def test_default_is_redis(self, router):
        """A function nothing was learned about goes to Redis."""
        assert router.route_for(FUN_NAME) is Route.REDIS

    def test_learn(self, router):
        """A learned route is returned from then on."""
        assert router.learn(FUN_NAME, Route.RAM_NOT_SHAREABLE, "value is a X") is True
        assert router.route_for(FUN_NAME) is Route.RAM_NOT_SHAREABLE

    def test_first_route_wins(self, router):
        """Learning again changes nothing."""
        router.learn(FUN_NAME, Route.RAM_NOT_SHAREABLE, "first")
        assert router.learn(FUN_NAME, Route.RAM_EXCLUDED, "second") is False
        assert router.route_for(FUN_NAME) is Route.RAM_NOT_SHAREABLE
        assert router.snapshot()[FUN_NAME]["reason"] == "first"

    def test_per_function(self, router):
        """Routes are per function."""
        router.learn("a.b", Route.RAM_NOT_SHAREABLE, "x")
        assert router.route_for("a.c") is Route.REDIS

    def test_logged_once(self, router, caplog):
        """A route is logged once, at INFO, with its reason."""
        caplog.set_level(logging.INFO, logger="collective.redismemoize")
        for _ in range(3):
            router.learn(FUN_NAME, Route.RAM_NOT_SHAREABLE, "value is a Thing")
        assert [r.getMessage() for r in caplog.records] == [
            f"{FUN_NAME}: values kept in RAM (ram-not-shareable): value is a Thing"
        ]
        assert caplog.records[0].levelno == logging.INFO

    def test_route_values(self):
        """The values the status endpoint reports."""
        assert [r.value for r in Route] == [
            "redis",
            "ram-excluded",
            "ram-not-shareable",
        ]


class TestCounters:
    def test_count(self, router):
        """Counters add up per function."""
        router.count(FUN_NAME, "redis_hits")
        router.count(FUN_NAME, "redis_hits")
        router.count(FUN_NAME, "errors")
        counters = router.snapshot()[FUN_NAME]["counters"]
        assert counters["redis_hits"] == 2
        assert counters["errors"] == 1
        assert counters["ram_hits"] == 0

    def test_unknown_counter(self, router):
        """A typo in a counter name is an error, not a silent new counter."""
        with pytest.raises(ValueError, match="unknown counter"):
            router.count(FUN_NAME, "hits")

    def test_snapshot_shape(self, router):
        """Every function seen, sorted, with every counter."""
        router.count("b.f", "ram_hits")
        router.learn("a.f", Route.RAM_EXCLUDED, "excluded")
        snapshot = router.snapshot()
        assert list(snapshot) == ["a.f", "b.f"]
        assert snapshot["a.f"]["route"] == "ram-excluded"
        assert snapshot["b.f"] == {
            "route": "redis",
            "reason": None,
            "counters": {counter: int(counter == "ram_hits") for counter in COUNTERS},
        }

    def test_reset(self, router):
        """``reset`` forgets everything."""
        router.count(FUN_NAME, "ram_hits")
        router.learn(FUN_NAME, Route.RAM_EXCLUDED, "x")
        router.reset()
        assert router.snapshot() == {}
        assert router.route_for(FUN_NAME) is Route.REDIS


class TestThreads:
    def test_concurrent_learning_and_counting(self):
        """Many threads learning and counting lose nothing and learn once."""
        router = Router()
        learned: list[bool] = []
        barrier = threading.Barrier(16)

        def work(index: int) -> None:
            barrier.wait()
            for _ in range(500):
                router.count(FUN_NAME, "refused")
            learned.append(
                router.learn(FUN_NAME, Route.RAM_NOT_SHAREABLE, f"thread {index}")
            )

        threads = [threading.Thread(target=work, args=(i,)) for i in range(16)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert learned.count(True) == 1
        assert router.snapshot()[FUN_NAME]["counters"]["refused"] == 16 * 500
