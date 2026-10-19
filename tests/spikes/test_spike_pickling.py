"""Why "pickle did not raise" cannot decide what is shareable."""

from Acquisition import Implicit
from persistent import Persistent

import io
import pickle
import pytest


class Content(Implicit):
    """A minimal acquisition-aware object."""


class PersistentThing(Persistent):
    """Stands in for content or a tool, without a wrapper."""


class Utility:
    """Stands in for a registered utility: a plain object."""


class RefusePersistent(pickle.Pickler):
    """A pickler that refuses persistent objects through ``persistent_id``."""

    def persistent_id(self, obj):
        if isinstance(obj, Persistent):
            raise TypeError(f"refusing {type(obj).__name__}")
        return None


def refuse_persistent(value) -> bytes:
    """Pickle with :class:`RefusePersistent`."""
    buffer = io.BytesIO()
    RefusePersistent(buffer, protocol=5).dump(value)
    return buffer.getvalue()


def test_acquisition_wrapper_raises():
    """A wrapped object is the one case pickle refuses on its own."""
    parent = Content()
    parent.child = Content()
    with pytest.raises(TypeError, match="Can't pickle objects in acquisition wrappers"):
        pickle.dumps(parent.child)


def test_persistent_pickles_into_a_detached_copy():
    """An unwrapped persistent object pickles, and comes back as a copy."""
    thing = PersistentThing()
    copy = pickle.loads(pickle.dumps(thing))
    assert copy is not thing
    assert type(copy) is PersistentThing


def test_utility_round_trips_into_another_object():
    """A component comes back as a different object, not the registered one."""
    utility = Utility()
    assert pickle.loads(pickle.dumps(utility)) is not utility


@pytest.mark.parametrize(
    "value,refused",
    [
        ([PersistentThing()], True),
        ({"lang": "en"}, False),
        ("<p>html</p>", False),
    ],
)
def test_persistent_id_hook(value, refused: bool):
    """A ``persistent_id`` hook can refuse persistent objects, but only those."""
    if refused:
        with pytest.raises(TypeError, match="refusing"):
            refuse_persistent(value)
    else:
        assert pickle.loads(refuse_persistent(value)) == value
