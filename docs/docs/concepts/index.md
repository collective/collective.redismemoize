---
myst:
  html_meta:
    "description": "How collective.redismemoize decides what to share, and why it behaves the way it does."
    "property=og:description": "How collective.redismemoize decides what to share, and why it behaves the way it does."
    "property=og:title": "Concepts"
    "keywords": "Plone, plone.memoize, Redis, concepts"
---

(concepts)=

# Concepts

These pages explain how the package works and why.
Read them away from the keyboard.

````{grid} 1 1 2 3
:gutter: 3

```{grid-item-card} 🧭 How plone.memoize picks a cache
:link: how-plone-memoize-picks-a-cache
:link-type: doc

The one hook the package replaces, and what it leaves alone.
```

```{grid-item-card} ✅ What "shareable" means
:link: what-shareable-means
:link-type: doc

Plain data goes to Redis; everything else stays in RAM.
```

```{grid-item-card} 🔀 Per-function routing
:link: per-function-routing
:link-type: doc

How each function learns where its values belong.
```

```{grid-item-card} 🛟 Failure model
:link: failure-model
:link-type: doc

What happens when Redis is slow, down, or full.
```

```{grid-item-card} 📋 Copies, not shared objects
:link: copies-not-shared-objects
:link-type: doc

Why a value read from Redis is a new object every time.
```

```{grid-item-card} 🔒 Security model
:link: security-model
:link-type: doc

Who can write to the cache, and what a reader can be made to run.
```

```{grid-item-card} 🗺️ Which Plone caches land where
:link: plone-caches
:link-type: doc

The cached functions in Plone, and the route each one takes.
```

```{grid-item-card} 🚫 When not to use it
:link: when-not-to-use
:link-type: doc

Single instances, and keys that leave something out.
```
````

```{toctree}
:maxdepth: 1
:hidden: true

how-plone-memoize-picks-a-cache
what-shareable-means
per-function-routing
failure-model
copies-not-shared-objects
security-model
plone-caches
when-not-to-use
```
