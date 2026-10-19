(concepts-when-not)=

# When not to use it

<!-- source: src/collective/redismemoize/adapter.py -->

## A single instance

A RAM cache lookup is a dictionary access.
A Redis lookup is a network round trip and a decode.
With one instance, there is nobody to share with, and Redis only adds latency.

## Keys that leave something out

Sharing is safe only when the {term}`cache key` captures everything the value depends on.
Within one process that is easy to get away with: the process itself is part of the context, even if the key never says so.
Across instances it is not.

Consider a function cached by the content's path alone, whose result also depends on the host name the request came in on.
In one process with one host name, the key is enough.
Behind a load balancer serving two host names, one instance computes the value for the first host name and the other instance serves it for the second.

The package cannot detect this.
The value is plain data, and the key is a valid key.
Two habits help:

- review the key functions of your own add-ons' `@ram.cache` functions for anything implicit: host name, language negotiation, the current user, environment variables;
- watch the routing table on the status endpoint after enabling the package, and exclude any function whose results look wrong.

The keys of the Plone caches the tests drive depend only on what their values depend on.
The i18n catalog is keyed by domain and language, the sitemap by site URL and catalog counter, the theming caches by theme and plugin count, and the page cache by URL and ETag.

## Values that must stay objects

Code that caches objects on purpose, a tool, a utility, or content, still works: those values are refused and stay in RAM.
It just gains nothing from the package.

## Related

- {doc}`/how-to-guides/include-and-exclude-functions`
- {doc}`/how-to-guides/monitor`
- {doc}`per-function-routing`
