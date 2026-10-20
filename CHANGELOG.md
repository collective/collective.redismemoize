# Changelog

<!--
   You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst
-->

<!-- towncrier release notes start -->

## 1.0.0a1 (2026-10-19)


### Feature

- Initial implementation: `plone.memoize` RAM cache values are stored in Redis or Valkey and shared across Plone instances, while values that are not plain data stay in each process's RAM cache. Includes per-function routing, a circuit breaker, a restricted unpickler, environment-based configuration, a Manager-only `@redismemoize` REST API endpoint for status and invalidation, and a test layer for add-ons. @ericof
