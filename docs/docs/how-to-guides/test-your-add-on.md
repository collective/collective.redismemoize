(how-to-test-your-add-on)=

# Test your add-on against Redis

<!-- source: src/collective/redismemoize/testing.py, tests/docs/snippets/integrator/ -->

This guide shows you how to run your add-on's tests with `@ram.cache` going through `collective.redismemoize`.
Use it to check that the values your functions cache are shareable, before a deploy finds out.

The tests use `fakeredis`, an in-process Redis, so they need no server.

## Add the test dependencies

Add `collective.redismemoize` and `fakeredis` to your add-on's test extra:

```toml
[project.optional-dependencies]
test = [
    "collective.redismemoize",
    "fakeredis",
]
```

## Add the layer

`REDIS_MEMOIZE_FIXTURE` loads the cache chooser and points it at a fake server.
Put it in the bases of a testing layer, after the Plone fixture.
With pytest and `pytest-plone`, in your `conftest.py`:

```{literalinclude} ../../../tests/docs/snippets/integrator/conftest.py
:language: python
```

## Write the tests

Every test starts with an empty fake server, an empty RAM cache, and no learned routes.
Plone's own cached functions may store values while the test's site is set up, so look for the keys of your function only.
The server is available as `REDIS_MEMOIZE_FIXTURE["redis_server"]`:

```{literalinclude} ../../../tests/docs/snippets/integrator/test_greeting.py
:language: python
```

The test suite of `collective.redismemoize` runs these two files as they are.

## Check that a value is shareable

To check one value without a Plone layer, pass it to the serializer:

```python
from collective.redismemoize import serializer

serializer.check(value)
```

`check` raises `NotShareable` for a value Redis would refuse, and its message names the part of the value at fault.

## Without layers

`collective.redismemoize.testing.activate()` and `deactivate()` do the same as the layer, for a pytest fixture or a test runner without layers.
`activate` returns the fake server.

## Related

- {doc}`/reference/api/testing`
- {doc}`/concepts/what-shareable-means`
