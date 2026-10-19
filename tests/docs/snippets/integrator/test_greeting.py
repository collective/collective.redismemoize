from collective.redismemoize.testing import REDIS_MEMOIZE_FIXTURE
from plone.memoize import ram

import fakeredis


CALLS = []


def _key(fun, lang):
    return lang


@ram.cache(_key)
def greeting(lang):
    CALLS.append(lang)
    return {"en": "Hello", "pt": "Olá"}[lang]


def stored_keys():
    """Return the keys Redis holds for ``greeting``."""
    client = fakeredis.FakeRedis(server=REDIS_MEMOIZE_FIXTURE["redis_server"])
    return client.keys("*:test_greeting.greeting:*")


def test_cached_in_redis(portal):
    assert greeting("en") == "Hello"
    assert greeting("en") == "Hello"
    assert CALLS == ["en"]
    assert len(stored_keys()) == 1


def test_each_test_starts_empty(portal):
    assert stored_keys() == []
    greeting("en")
    assert CALLS == ["en", "en"]
