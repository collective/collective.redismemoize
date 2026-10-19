---
myst:
  html_meta:
    "description": "Reference for collective.redismemoize: environment variables, REST API, Python API, ZCML, log messages, and compatibility."
    "property=og:description": "Reference for collective.redismemoize: environment variables, REST API, Python API, ZCML, log messages, and compatibility."
    "property=og:title": "Reference"
---

(reference)=

# Reference

This part of the documentation describes the package's interfaces: the environment variables it reads, the endpoints and functions it provides, what it registers, and what it logs.

````{grid} 1 1 2 3
:gutter: 3

```{grid-item-card} ⚙️ Configuration
:link: configuration
:link-type: doc

Every environment variable, its default, and what it accepts.
```

```{grid-item-card} 🌐 REST API
:link: rest-api
:link-type: doc

The `@redismemoize` status and invalidation endpoints.
```

```{grid-item-card} 🐍 Python API
:link: python-api
:link-type: doc

The modules, from `api` and `testing` to the internals.
```

```{grid-item-card} 🧩 ZCML
:link: zcml
:link-type: doc

What the package registers, and how to load it.
```

```{grid-item-card} 📝 Log messages
:link: log-messages
:link-type: doc

Every message the package logs, and when.
```

```{grid-item-card} 🔗 Compatibility
:link: compatibility
:link-type: doc

Plone, Python, Redis, Valkey, and redis-py versions.
```
````

```{toctree}
:maxdepth: 1
:hidden: true

configuration
rest-api
python-api
zcml
log-messages
compatibility
```
