(concepts-chooser)=

# How `plone.memoize` picks a cache

<!-- source: plone/memoize/ram.py, plone/memoize/volatile.py, src/collective/redismemoize/chooser.py -->

`plone.memoize.ram.cache` is a decorator.
Every call of a decorated function asks the decorator's key function for a key, prefixes it with the function's dotted name, and looks that {term}`cache key` up in a mapping.
On a miss, the function runs and its result is stored under the key.

The mapping does not come from the decorator.
It comes from a {term}`cache chooser`: the utility registered for `plone.memoize.interfaces.ICacheChooser`, which `plone.memoize` calls with the function's dotted name, `plone.app.content.browser.i18n._gettext_catalog` for example.
Stock Plone registers `plone.memoize.ram.choose_cache`, which answers with an adapter over the process-local `zope.ramcache` cache.
So every Plone process keeps its own copy of every cached value, and the copies never meet.

`plone.app.caching` uses the same utility for its RAM page cache, under the name `plone.app.caching.operations.ramcache`.

## One utility, replaced once

This package registers its own chooser in `overrides.zcml`, in place of the stock one.
Nothing in the decorated functions changes, and nothing in the add-ons that define them.
Plone's own `@ram.cache` functions, those of every add-on, and the RAM page cache all go through it.

The replacement is global to the process, not per site.
A cached function runs outside any particular site, the first time it is called, and its cache is the same object for every site in the process.
That is why the configuration comes from the environment rather than from the Plone registry, and why the package has no GenericSetup profile to install.

## What the new chooser answers

For each function, the chooser answers with one of two things.

- When no Redis URL is configured, or the configuration excludes the function, it answers exactly what the stock chooser answers: an adapter over the same RAM cache.
- Otherwise it answers a Redis adapter, which wraps that same RAM adapter and falls back to it.

The Redis adapter decides, value by value, whether a value goes to Redis or stays in RAM.
{doc}`what-shareable-means` explains that decision.

## Related

- {doc}`/reference/zcml`
- {doc}`/how-to-guides/install`
- {doc}`per-function-routing`
