(reference-log-messages)=

# Log messages

<!-- source: src/collective/redismemoize/client.py, routing.py -->

The package logs to the `collective.redismemoize` logger.
`%s` stands for a value filled in at run time.

## Messages

| Level | Message | When |
| --- | --- | --- |
| `WARNING` | `Redis unavailable (%s: %s); using the RAM cache for %ss` | A call to Redis failed and the breaker opened. Logged once per opening, with the exception's type and text, and `REDIS_MEMOIZE_RETRY_AFTER`. |
| `INFO` | `Redis available again; values are shared again` | A call to Redis succeeded after the breaker had opened. |
| `INFO` | `%s: values kept in RAM (%s): %s` | A function got a RAM route. Logged once per function and process, with the function's name, the route, and the reason. |

The test suite checks that each message in this table is in the code.

## Related

- {doc}`/how-to-guides/monitor`
- {doc}`/concepts/failure-model`
