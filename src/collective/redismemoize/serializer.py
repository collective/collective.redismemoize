"""Strict serialization of plain data.

A value goes to Redis only when it is *plain data*, and that is decided by
construction: :func:`dumps` walks the value and accepts nothing but the types
listed here, matched exactly. "``pickle.dumps`` did not raise" is not the test.
A persistent object without an acquisition wrapper pickles happily and comes
back as a detached copy, and a utility comes back as a different object.
Neither is an error pickle can report, and both break the caller.

:func:`loads` is the security boundary. Its unpickler resolves only the
globals the accepted types need, so a payload someone else wrote into Redis
cannot make this process call anything.

This module is pure Python and never imports Zope; ``DateTime`` is a plain
library.
"""

from DateTime import DateTime

import datetime
import decimal
import io
import pickle
import uuid


#: First byte of every payload. A future format gets a new byte, and a payload
#: with a byte this code does not know is treated as a miss.
FORMAT_VERSION = b"\x01"

#: Pickle protocol used for every payload.
PROTOCOL = 5

#: Types accepted as leaves, matched with ``type(value) in LEAVES``.
LEAVES: frozenset[type] = frozenset({
    str,
    bytes,
    bytearray,
    int,
    float,
    complex,
    bool,
    type(None),
    decimal.Decimal,
    datetime.date,
    datetime.time,
    datetime.datetime,
    datetime.timedelta,
    datetime.timezone,
    DateTime,
    uuid.UUID,
})

#: Containers accepted, walked recursively, matched exactly.
SEQUENCES: frozenset[type] = frozenset({list, tuple, set, frozenset})

#: The globals :func:`loads` may resolve, as ``(module, name)``. Exactly what
#: pickling the types in :data:`LEAVES` produces, and nothing else.
SAFE_GLOBALS: frozenset[tuple[str, str]] = frozenset({
    ("builtins", "complex"),
    ("decimal", "Decimal"),
    ("datetime", "date"),
    ("datetime", "time"),
    ("datetime", "datetime"),
    ("datetime", "timedelta"),
    ("datetime", "timezone"),
    ("DateTime.DateTime", "DateTime"),
    ("uuid", "UUID"),
})


class NotShareable(TypeError):
    """A value that is not plain data, and so stays in the RAM cache.

    :param reason: What was refused and where, for the log.
    """

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class UndecodableValue(ValueError):
    """A payload :func:`loads` refuses to decode; callers treat it as a miss."""


def _type_name(value: object) -> str:
    """Return the dotted name of a value's type.

    :param value: Any object.
    :returns: ``module.QualifiedName``.
    """
    kind = type(value)
    return f"{kind.__module__}.{kind.__qualname__}"


def check(value: object, path: str = "value") -> None:
    """Refuse anything that is not plain data.

    :param value: The value to check.
    :param path: Where ``value`` sits in the structure, for the message.
    :raises NotShareable: Naming the offending type and its path.
    """
    _check(value, path, set())


def _check(value: object, path: str, ancestors: set[int]) -> None:
    """Walk one node of a value.

    :param value: The node.
    :param path: Its path from the root.
    :param ancestors: Ids of the containers above it, to refuse cycles.
    :raises NotShareable: When the node or anything below it is refused.
    """
    kind = type(value)
    if kind in LEAVES:
        if kind in (datetime.datetime, datetime.time):
            tzinfo = value.tzinfo  # type: ignore[attr-defined]
            if tzinfo is not None and type(tzinfo) is not datetime.timezone:
                raise NotShareable(
                    f"{path} has tzinfo of type {_type_name(tzinfo)}; "
                    "only None and datetime.timezone are plain data"
                )
        return
    if kind not in SEQUENCES and kind is not dict:
        raise NotShareable(f"{path} is a {_type_name(value)}")
    if id(value) in ancestors:
        raise NotShareable(f"{path} contains itself")
    ancestors.add(id(value))
    if kind is dict:
        for key, item in value.items():  # type: ignore[attr-defined]
            _check(key, f"{path} key {key!r}", ancestors)
            _check(item, f"{path}[{key!r}]", ancestors)
    else:
        for index, item in enumerate(value):  # type: ignore[call-overload]
            _check(item, f"{path}[{index}]", ancestors)
    ancestors.discard(id(value))


def dumps(value: object) -> bytes:
    """Serialize plain data.

    :param value: The value to store.
    :returns: The payload, starting with :data:`FORMAT_VERSION`.
    :raises NotShareable: When the value is not plain data.
    """
    try:
        check(value)
    except RecursionError:
        raise NotShareable("value is nested too deeply") from None
    return FORMAT_VERSION + pickle.dumps(value, protocol=PROTOCOL)


class _RestrictedUnpickler(pickle.Unpickler):
    """An unpickler that resolves only :data:`SAFE_GLOBALS`."""

    def find_class(self, module: str, name: str) -> type:
        """Resolve a global, if it is one plain data needs.

        :param module: Module of the global.
        :param name: Its name.
        :returns: The class.
        :raises pickle.UnpicklingError: For any other global.
        """
        if (module, name) not in SAFE_GLOBALS:
            raise pickle.UnpicklingError(f"global {module}.{name} is not allowed")
        return super().find_class(module, name)


def loads(payload: bytes) -> object:
    """Decode a payload written by :func:`dumps`.

    :param payload: The bytes read from Redis.
    :returns: A new copy of the stored value.
    :raises UndecodableValue: For an unknown format, a truncated or corrupt
        payload, or one that asks for a global not in :data:`SAFE_GLOBALS`.
    """
    if payload[:1] != FORMAT_VERSION:
        raise UndecodableValue(f"unknown format byte {payload[:1]!r}")
    try:
        return _RestrictedUnpickler(io.BytesIO(payload[1:])).load()
    except Exception as exc:
        # Anything at all: a corrupt payload can make the unpickler raise
        # almost any exception type, and every one of them means a miss.
        raise UndecodableValue(f"{type(exc).__name__}: {exc}") from exc
