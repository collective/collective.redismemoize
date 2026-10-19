---
myst:
  html_meta:
    "description": "Share plone.memoize RAM caches between Plone instances through Redis or Valkey, while values that cannot be shared safely stay in each process."
    "property=og:description": "Share plone.memoize RAM caches between Plone instances through Redis or Valkey, while values that cannot be shared safely stay in each process."
    "property=og:title": "collective.redismemoize"
    "keywords": "Plone, plone.memoize, Redis, Valkey, cache"
---

(index)=

# collective.redismemoize

`collective.redismemoize` stores the values of `plone.memoize`'s RAM cache in Redis or Valkey, so every Plone instance that talks to the same server shares them.
Values that are not plain data, such as content objects, utilities, or anything holding a database connection, stay in each process's own RAM cache, exactly where stock Plone keeps them.

Install it, set one environment variable, and every `@ram.cache` function in Plone and in your add-ons goes through it.
Without that variable, the package changes nothing.

## When to use it

Use it when you run several Plone instances behind a load balancer, and each instance computes the same cached values on its own.
A shared cache means one instance computes a value and the others reuse it, and a new instance starts warm.

## When not to use it

Do not use it for a single instance: the RAM cache is faster than any network round trip.
Do not use it to share values whose cache key leaves out something that differs between instances.
{doc}`concepts/when-not-to-use` explains both cases.

## Where to start

````{grid} 1 1 2 2
:gutter: 3

```{grid-item-card} 🎓 Tutorials
:link: tutorials/index
:link-type: doc

See it work in fifteen minutes: share a cache between two instances on your computer.
```

```{grid-item-card} 🛠️ How-to guides
:link: how-to-guides/index
:link-type: doc

Install, configure, monitor, invalidate, and test your add-on against Redis.
```

```{grid-item-card} 💡 Concepts
:link: concepts/index
:link-type: doc

What the package shares, what it refuses, and why it fails safe.
```

```{grid-item-card} 📖 Reference
:link: reference/index
:link-type: doc

Environment variables, REST API, Python API, ZCML, and log messages.
```
````


```{toctree}
:caption: Table of Contents
:maxdepth: 2
:hidden: true

tutorials/index
how-to-guides/index
concepts/index
reference/index
```

```{toctree}
:caption: Appendices
:maxdepth: 1
:hidden: true

glossary
genindex
```
