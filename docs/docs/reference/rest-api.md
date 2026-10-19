(reference-rest-api)=

# REST API

<!-- source: src/collective/redismemoize/services/, tests/docs/test_rest_examples.py -->

The package adds one endpoint, `@redismemoize`, on the Plone site root.
It requires the `Manage portal` permission, which only the Manager role has in a stock Plone 6.2 site.
Site Administrators get `401 Unauthorized`.

Every instance answers for itself.
The breaker, the routes and the counters belong to the process that handled the request.

The examples below are recorded by the test suite.

## Get the status

`GET /@redismemoize` returns the configuration, the state of the breaker, the server, and every cached function the process has seen.

```{eval-rst}
.. http:example:: curl httpie python-requests
   :request: ../../../tests/docs/http-examples/status_get.req
```

```{literalinclude} ../../../tests/docs/http-examples/status_get.resp
:language: http
```

The response has these keys:

`active`
:   `true` when `REDIS_MEMOIZE_URL` is set.

`settings`
:   The configuration in effect, with any password in the URL replaced by `***`.

`breaker`
:   `open`, and `seconds_until_retry`; `null` when the package is inert.

`server`
:   `latency_ms` of a `PING`, `product` (`redis` or `valkey`), `version`, and `error`; `null` when the package is inert.
    The endpoint contacts the server even while the breaker is open.

`functions`
:   For each function, its `route`, the `reason` for a RAM route, and its `counters`.

The routes are:

`redis`
:   Values go to Redis.

`ram-excluded`
:   An include or exclude pattern keeps the function in RAM.

`ram-not-shareable`
:   A value was not shareable; the function stays in RAM until the process restarts.

The counters are `redis_hits`, `redis_misses`, `ram_hits`, `ram_misses`, `refused`, `too_large`, `undecodable`, and `errors`.

Without `REDIS_MEMOIZE_URL`, the response says so:

```{literalinclude} ../../../tests/docs/http-examples/status_get_inactive.resp
:language: http
```

## Invalidate one function

`POST /@redismemoize/invalidate` with a body naming a function drops that function's values from Redis, and from the RAM cache of the instance that answers.

```{eval-rst}
.. http:example:: curl httpie python-requests
   :request: ../../../tests/docs/http-examples/invalidate_function.req
```

```{literalinclude} ../../../tests/docs/http-examples/invalidate_function.resp
:language: http
```

`removed` is the number of Redis keys removed.

## Invalidate everything

`POST /@redismemoize/invalidate` with an empty object as the body drops every key under the prefix, and the whole RAM cache of the instance that answers.

```{eval-rst}
.. http:example:: curl httpie python-requests
   :request: ../../../tests/docs/http-examples/invalidate_all.req
```

```{literalinclude} ../../../tests/docs/http-examples/invalidate_all.resp
:language: http
```

## Errors

`400 Bad Request`
:   The body is not a JSON object, or `function` is not a non-empty string.

`401 Unauthorized`
:   The user lacks `Manage portal`.

`404 Not Found`
:   A `POST` to any path other than `@redismemoize/invalidate`.

## Related

- {doc}`/how-to-guides/monitor`
- {doc}`/how-to-guides/invalidate-after-a-deploy`
