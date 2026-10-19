---
myst:
  html_meta:
    "description": "Task-oriented guides to install, configure, operate, and test collective.redismemoize."
    "property=og:description": "Task-oriented guides to install, configure, operate, and test collective.redismemoize."
    "property=og:title": "How-to guides"
    "keywords": "Plone, plone.memoize, Redis, how-to"
---

(how-to-guides)=

# How-to guides

These guides solve one task each, for a project that already runs Plone.

````{grid} 1 1 2 3
:gutter: 3

```{grid-item-card} 📦 Install the package
:link: install
:link-type: doc

Add the dependency, and load the ZCML with or without autoinclude.
```

```{grid-item-card} ⚙️ Configure Redis
:link: configure
:link-type: doc

Point Plone at Redis, and run Redis as a private, bounded cache.
```

```{grid-item-card} 🔁 Use Valkey
:link: use-valkey
:link-type: doc

Swap Redis for Valkey without changing the URL scheme.
```

```{grid-item-card} 🎯 Include and exclude functions
:link: include-and-exclude-functions
:link-type: doc

Choose which cached functions may use Redis.
```

```{grid-item-card} ⏱️ Give a function its own TTL
:link: give-a-function-its-own-ttl
:link-type: doc

Cache a function of your add-on for a lifetime of its own.
```

```{grid-item-card} 🧹 Invalidate after a deploy
:link: invalidate-after-a-deploy
:link-type: doc

Drop values that new code computes differently.
```

```{grid-item-card} 📊 Monitor the cache
:link: monitor
:link-type: doc

Read the status endpoint, the counters, and the logs.
```

```{grid-item-card} 🧪 Test your add-on
:link: test-your-add-on
:link-type: doc

Run your add-on's tests against a fake Redis.
```

```{grid-item-card} 🩺 Troubleshoot
:link: troubleshoot
:link-type: doc

Find the cause of the most common problems.
```
````

```{toctree}
:maxdepth: 1
:hidden: true

install
configure
use-valkey
include-and-exclude-functions
give-a-function-its-own-ttl
invalidate-after-a-deploy
monitor
test-your-add-on
troubleshoot
```
