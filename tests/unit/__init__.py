"""Pure Python tests: no Plone layer, Redis replaced by ``fakeredis``."""

from DateTime import DateTime
from decimal import Decimal

import datetime
import uuid


class Clock:
    """A monotonic clock the test moves by hand."""

    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        """Return the current time.

        :returns: Seconds.
        """
        return self.now

    def advance(self, seconds: float) -> None:
        """Move the clock forward.

        :param seconds: How far.
        """
        self.now += seconds


#: One value of every leaf type the serializer accepts.
LEAF_VALUES = [
    "text",
    "",
    "ãçé",
    b"\x00bytes",
    bytearray(b"mutable"),
    0,
    -(2**80),
    1.5,
    float("inf"),
    3 + 4j,
    True,
    False,
    None,
    Decimal("10.25"),
    datetime.date(2026, 10, 19),
    datetime.time(12, 30),
    datetime.time(12, 30, tzinfo=datetime.timezone.utc),
    datetime.datetime(2026, 10, 19, 12, 30),
    datetime.datetime(
        2026, 10, 19, 12, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=-3))
    ),
    datetime.timedelta(days=1, seconds=2),
    datetime.timezone.utc,
    DateTime("2026/10/19 12:30:00 GMT-3"),
    uuid.UUID("55c25ebc-220d-4003-9357-4f37d648727c"),
]

#: Containers, nested, holding leaves.
NESTED_VALUES = [
    [],
    (),
    {},
    set(),
    frozenset(),
    [1, "two", (3.0, None)],
    {"lang": "en", "items": [{"id": 1}, {"id": 2}]},
    {1: "int key", (1, 2): "tuple key", None: "none key"},
    {frozenset({1}), (1, "a")},
    {"nested": {"deeper": {"deepest": [Decimal("1"), DateTime("2026/01/01")]}}},
    (200, {"content-type": "text/html"}, b"<p>body</p>", True),
]
