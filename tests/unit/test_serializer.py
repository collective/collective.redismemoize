"""The strict serializer: plain data in, everything else refused."""

from . import LEAF_VALUES
from . import NESTED_VALUES
from Acquisition import Implicit
from collections import OrderedDict
from collective.redismemoize import serializer
from collective.redismemoize.serializer import dumps
from collective.redismemoize.serializer import FORMAT_VERSION
from collective.redismemoize.serializer import loads
from collective.redismemoize.serializer import NotShareable
from collective.redismemoize.serializer import UndecodableValue
from pathlib import Path
from persistent import Persistent
from persistent.mapping import PersistentMapping
from zope.i18nmessageid import MessageFactory
from zope.interface import Interface

import datetime
import enum
import os
import pickle
import pytest
import zoneinfo


#: Calls recorded by :func:`sentinel`.
CALLS: list[str] = []


def sentinel(marker: str) -> None:
    """Record that a payload managed to call something.

    :param marker: What to record.
    """
    CALLS.append(marker)


class CallsSentinel:
    """Pickles into a call of :func:`sentinel`."""

    def __reduce__(self):
        return (sentinel, ("called",))


class RunsShellCommand:
    """Pickles into ``os.system(command)``."""

    def __init__(self, command: str):
        self.command = command

    def __reduce__(self):
        return (os.system, (self.command,))


class Content(Implicit):
    """A minimal acquisition-aware object."""


class PersistentThing(Persistent):
    """A persistent object, as content and tools are."""


class Color(enum.IntEnum):
    RED = 1


class MyDict(dict):
    pass


class MyList(list):
    pass


class MyStr(str):
    pass


def _wrapped() -> Content:
    parent = Content()
    parent.child = Content()
    return parent.child


_ = MessageFactory("plone")

#: Values that must be refused, with a substring of the reason.
REFUSED = [
    (PersistentThing(), "PersistentThing"),
    (PersistentMapping({"a": 1}), "PersistentMapping"),
    (_wrapped(), "ImplicitAcquisitionWrapper"),
    (Interface, "InterfaceClass"),
    (sentinel, "function"),
    (lambda: None, "function"),
    (Content, "ExtensionClass"),
    (os, "module"),
    ((item for item in ()), "generator"),
    (_("Hello"), "Message"),
    (MyDict(a=1), "MyDict"),
    (MyList([1]), "MyList"),
    (MyStr("x"), "MyStr"),
    (OrderedDict(a=1), "OrderedDict"),
    (Color.RED, "Color"),
    (object(), "builtins.object"),
    (
        datetime.datetime(2026, 1, 1, tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")),
        "ZoneInfo",
    ),
    (datetime.time(1, tzinfo=zoneinfo.ZoneInfo("UTC")), "ZoneInfo"),
]


class TestRoundTrip:
    @pytest.mark.parametrize("value", LEAF_VALUES, ids=repr)
    def test_leaf(self, value):
        """Every accepted leaf type survives a round trip, type included."""
        result = loads(dumps(value))
        assert result == value
        assert type(result) is type(value)

    @pytest.mark.parametrize("value", NESTED_VALUES, ids=repr)
    def test_nested(self, value):
        """Containers of accepted types survive a round trip."""
        result = loads(dumps(value))
        assert result == value
        assert type(result) is type(value)

    def test_every_leaf_together(self):
        """All the leaves at once, in one structure."""
        value = {"leaves": list(LEAF_VALUES[:-1]), "uuid": LEAF_VALUES[-1]}
        assert loads(dumps(value)) == value

    def test_shared_reference_is_not_a_cycle(self):
        """The same list twice in a structure is fine."""
        shared = [1, 2]
        assert loads(dumps([shared, shared])) == [[1, 2], [1, 2]]

    def test_result_is_a_copy(self):
        """What comes back is a new object, not the one stored."""
        value = {"a": [1]}
        result = loads(dumps(value))
        assert result == value
        assert result is not value
        assert result["a"] is not value["a"]

    def test_format_byte(self):
        """Every payload starts with the format version."""
        assert dumps("x")[:1] == FORMAT_VERSION == b"\x01"


class TestRefusal:
    @pytest.mark.parametrize("value,fragment", REFUSED, ids=lambda v: type(v).__name__)
    def test_refused(self, value, fragment: str):
        """Anything that is not plain data raises NotShareable."""
        with pytest.raises(NotShareable) as info:
            dumps(value)
        assert fragment in info.value.reason

    @pytest.mark.parametrize("value,fragment", REFUSED, ids=lambda v: type(v).__name__)
    def test_refused_when_nested(self, value, fragment: str):
        """A refused value deep inside a structure refuses the whole value."""
        with pytest.raises(NotShareable) as info:
            dumps({"items": [1, 2, (3, value)]})
        assert fragment in info.value.reason
        assert "value['items'][2][1]" in info.value.reason

    def test_unpicklable_by_plain_pickle_too(self):
        """Control: plain pickle accepts a detached persistent object.

        That is exactly why "pickle did not raise" cannot be the test.
        """
        thing = PersistentThing()
        copy = pickle.loads(pickle.dumps(thing))
        assert copy is not thing

    def test_reason_names_type_and_path(self):
        """The reason names both the offending type and where it was."""
        with pytest.raises(NotShareable) as info:
            dumps([{"portlet": PersistentThing()}])
        assert info.value.reason == (
            "value[0]['portlet'] is a tests.unit.test_serializer.PersistentThing"
        )

    def test_refused_dict_key(self):
        """Keys are checked too."""
        with pytest.raises(NotShareable) as info:
            dumps({Color.RED: 1})
        assert "key" in info.value.reason

    def test_cycle(self):
        """A structure containing itself is refused."""
        value: list = [1]
        value.append(value)
        with pytest.raises(NotShareable, match="contains itself"):
            dumps(value)

    def test_too_deep(self):
        """A structure too deep to walk is refused, not a crash."""
        value: list = []
        for _ in range(100_000):
            value = [value]
        with pytest.raises(NotShareable, match="too deeply"):
            dumps(value)

    def test_not_shareable_is_a_type_error(self):
        """``NotShareable`` subclasses ``TypeError``, as pickle's own error."""
        assert issubclass(NotShareable, TypeError)


class TestSecurity:
    def test_payload_is_live_for_plain_pickle(self):
        """Control: plain ``pickle.loads`` does call the sentinel."""
        CALLS.clear()
        pickle.loads(pickle.dumps(CallsSentinel()))
        assert CALLS == ["called"]
        CALLS.clear()

    def test_restricted_unpickler_calls_nothing(self):
        """A payload naming a function is refused, and the function never runs."""
        CALLS.clear()
        payload = FORMAT_VERSION + pickle.dumps(CallsSentinel(), protocol=5)
        with pytest.raises(UndecodableValue, match="not allowed"):
            loads(payload)
        assert CALLS == []

    def test_os_system_never_runs(self, tmp_path: Path):
        """A crafted ``os.system`` payload is refused and runs no command."""
        target = tmp_path / "pwned"
        payload = FORMAT_VERSION + pickle.dumps(
            RunsShellCommand(f"touch {target}"), protocol=5
        )
        with pytest.raises(UndecodableValue, match="not allowed"):
            loads(payload)
        assert not target.exists()

    @pytest.mark.parametrize(
        "module,name",
        [
            ("builtins", "eval"),
            ("builtins", "getattr"),
            ("os", "system"),
            ("subprocess", "Popen"),
            ("collections", "OrderedDict"),
        ],
    )
    def test_find_class_refuses(self, module: str, name: str):
        """Globals outside the allowlist are refused by name."""
        unpickler = serializer._RestrictedUnpickler(__import__("io").BytesIO(b""))
        with pytest.raises(pickle.UnpicklingError, match=f"{module}.{name}"):
            unpickler.find_class(module, name)

    @pytest.mark.parametrize("module,name", sorted(serializer.SAFE_GLOBALS))
    def test_find_class_allows(self, module: str, name: str):
        """Every allowlisted global resolves."""
        unpickler = serializer._RestrictedUnpickler(__import__("io").BytesIO(b""))
        assert unpickler.find_class(module, name).__name__ == name


class TestUndecodable:
    @pytest.mark.parametrize(
        "payload",
        [
            b"",
            b"\x02" + pickle.dumps("x", protocol=5),
            pickle.dumps("x", protocol=5),
            dumps({"a": [1, 2, 3]})[:-5],
            FORMAT_VERSION + b"not a pickle",
            FORMAT_VERSION,
        ],
        ids=[
            "empty",
            "unknown-version",
            "no-version",
            "truncated",
            "garbage",
            "only-version",
        ],
    )
    def test_undecodable(self, payload: bytes):
        """Unknown formats and corrupt payloads raise UndecodableValue."""
        with pytest.raises(UndecodableValue):
            loads(payload)
