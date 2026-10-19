# Security policy

## Supported versions

This package is pre-release. Until 1.0.0, only the latest release is
supported.

## Reporting a vulnerability

Please report security issues **privately**, not in the public issue tracker.

Contact: `admins@plone.org`

Please include:

- what the issue is and what an attacker can do with it;
- the version or commit you found it in;
- steps to reproduce, if you have them.

You will get an acknowledgement within a few working days, and we will keep
you informed while we work on a fix.

## Threat model

Every Plone instance reads back what is stored in Redis, and turns it into
Python objects. Values are pickles, and an ordinary pickle can make its reader
call any function it names. This package reads them with a restricted
unpickler that resolves only the classes plain data needs; anything else makes
the value unreadable, and it is treated as a cache miss. Code execution in
Plone through a value written to Redis is in scope, and is the most serious
issue you can report.

Whoever can write to Redis can still poison the cache: a value stored under a
function's key is served as that function's result until it expires. That is
why Redis must be reachable only by the Plone instances, as the documentation
describes. A Redis server exposed to untrusted clients is a deployment error,
not a vulnerability in this package. A bypass of the shareability check that
puts a value in Redis which another instance then reads differently is in
scope.

The `@redismemoize` REST API endpoint requires the `Manage portal`
permission. Anything that lets another role read its status, which includes
the Redis URL with the password removed, or invalidate values, is in scope, as
is a password appearing in a log or a response.
