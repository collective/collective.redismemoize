(how-to-troubleshoot)=

# Troubleshoot

<!-- source: src/collective/redismemoize/config.py, client.py, routing.py, adapter.py -->

This guide shows you how to find the cause of the most common problems.
Start with the status endpoint, as {doc}`monitor` describes.

## Plone does not start

The traceback ends with a `ValueError` naming a `REDIS_MEMOIZE_*` variable.
Fix that variable; {doc}`/reference/configuration` lists the values each one accepts.

## `active` is `false`

`REDIS_MEMOIZE_URL` is not in the environment of the Plone process.
Check the environment of the container or service, not of your shell.

## The status endpoint answers 404

The package's ZCML is not loaded.
If your site disables autoinclude, include it as {doc}`install` describes.

## Nothing reaches Redis

Check, in this order:

1. `breaker.open` is `true`: the instance cannot reach Redis.
   Read `server.error`, and the `WARNING` in the instance's log.
2. The function's route is `ram-excluded`: an include or exclude pattern keeps it in RAM.
   Its `reason` names the pattern.
3. The function's route is `ram-not-shareable`: its values are not plain data.
   Its `reason` names the part of the value at fault.
4. The function is not listed at all: it was not called in this process since the start, or it is not cached through `plone.memoize`.

## A function stays in RAM, and it should not

The route `ram-not-shareable` lasts until the process restarts.
The log has an `INFO` line with the reason, such as `value['portlet'] is a my.addon.Portlet`.
Change the function to return plain data, as {doc}`/concepts/what-shareable-means` describes, and restart.

## `undecodable` grows

Instances that run different code share one prefix, and one stores values the other cannot read.
This is expected during a rolling deploy, and stops when every instance runs the new code.
If it does not stop, give each version its own `REDIS_MEMOIZE_PREFIX`.

## Instances show different values

Some value in the cache depends on something its key leaves out, such as a setting that differs between instances.
Exclude that function, as {doc}`include-and-exclude-functions` describes, and read {doc}`/concepts/when-not-to-use`.

## Old values survive a deploy

They live in Redis until their TTL runs out.
Invalidate them, as {doc}`invalidate-after-a-deploy` describes.

## Related

- {doc}`/reference/log-messages`
- {doc}`/concepts/failure-model`
