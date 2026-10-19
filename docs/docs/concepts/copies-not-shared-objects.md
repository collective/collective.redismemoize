(concepts-copies)=

# Copies, not shared objects

<!-- source: src/collective/redismemoize/adapter.py -->

The RAM cache hands every caller the same object.
A caller that changes a cached list or dictionary changes it for every later caller in that process, until the value expires.
That is rarely intended, and the bugs it causes are hard to find.

A value read from Redis is decoded anew on every hit, so every caller gets its own copy.
Changing it changes nothing in the cache.

For almost all code this is invisible, or a fix.
Code that relied on mutating a cached value to update the cache will see its change disappear on the next call; it was never safe across instances anyway.

Values routed to RAM still behave as before, which is how they keep working for objects that must not be copied.

## Related

- {doc}`per-function-routing`
- {doc}`what-shareable-means`
