(concepts-shareable)=

# What "shareable" means

<!-- source: src/collective/redismemoize/serializer.py, tests/spikes/test_spike_pickling.py -->

A value can go to Redis only if another process can read it back and get something equivalent.
For a cache, equivalent means the same answer the function would have computed there.

## Why pickle cannot decide

The obvious test is to pickle the value and see whether pickling fails.
It does not work, because pickle refuses very little.

- An object in an acquisition wrapper does fail: `TypeError: Can't pickle objects in acquisition wrappers.`
- A persistent object without a wrapper pickles fine, and comes back as a detached copy with no database connection: not the object the function returned, and not one that can be saved.
- A utility, or any other component, pickles fine and comes back as a different object than the one registered in the other process.

Neither of the last two is an error pickle can report, and both would hand the caller something subtly wrong.
The test suite pins all three behaviors, so a change in them fails a test rather than a site.

## Plain data, decided by construction

So the package does not ask whether a value pickles.
It walks the value and accepts only {term}`plain data`:

- strings, bytes, numbers, Booleans, and `None`;
- `Decimal`, the `datetime` types, Zope's `DateTime`, and `UUID`;
- lists, tuples, sets, frozen sets, and dictionaries of those, nested to any depth.

Types match exactly.
A subclass of `dict` or `str` is refused, because a subclass can carry anything.
That includes `zope.i18nmessageid.Message`, the translatable string Plone uses everywhere: it is a `str` carrying a translation domain and a default, and turning it into a plain string would drop them.
A `datetime` must be naive or carry a `datetime.timezone`; a `zoneinfo` or `pytz` zone is refused, because reading it back needs code this package does not allow a payload to call.

When a value is refused, the reason names the offending type and where it sits in the structure, for example `value[0][1] is a my.addon.plugins.ThemePlugin`.
That reason goes to the log and to the status endpoint.

## What happens to a refused value

It goes to the RAM cache, where stock Plone would have put it, and the function is routed to RAM for the rest of the process.
{doc}`per-function-routing` explains why the whole function, and not only that value.

## Related

- {doc}`security-model`
- {doc}`plone-caches`
- {doc}`/reference/api/serializer`
