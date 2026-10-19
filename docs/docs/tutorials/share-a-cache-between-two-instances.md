(tutorial-two-instances)=

# Share a cache between two instances

<!-- source: Makefile, instance.yaml, scripts/create_site.py; steps verified end to end against Plone 6.2 and Redis 7.4 -->

In this tutorial, we will run Redis and two Plone instances on your computer.
One instance will compute a cached value, and the other will read it from Redis instead of computing it again.

You need `git`, `make`, `uv`, Docker, and `curl`.
It takes about fifteen minutes, most of it spent installing Plone.

## Get the code

Clone the repository and install it:

```shell
git clone https://github.com/collective/collective.redismemoize.git
cd collective.redismemoize
make install
```

`make install` creates a virtual environment with Plone and the package, and the configuration of a first instance in `instance/`.

## Create the first site

Create a Plone site in the first instance:

```shell
make create-site
```

The command ends without output when the site exists.

## Create the second instance

Create the configuration of a second instance, listening on port 8081, in `instance-two/`:

```shell
uvx cookiecutter -f --no-input -c 3.1.0 --config-file instance.yaml gh:plone/cookiecutter-zope-instance target=instance-two wsgi_listen=localhost:8081
```

Then create a site in it:

```shell
.venv/bin/zconsole run instance-two/etc/zope.conf scripts/create_site.py
```

The two instances have separate databases.
The only thing they share will be Redis.

## Start Redis

Start Redis in a container, listening on port 6379:

```shell
docker run --rm --detach --name redismemoize-tutorial --publish 6379:6379 redis:7-alpine
```

## Start both instances

In one terminal, start the first instance with the Redis URL in its environment:

```shell
REDIS_MEMOIZE_URL=redis://localhost:6379/0 make start
```

In a second terminal, in the same directory, start the second instance:

```shell
REDIS_MEMOIZE_URL=redis://localhost:6379/0 .venv/bin/runwsgi instance-two/etc/zope.ini
```

Wait until both terminals show `Serving on`.

## Compute a value on the first instance

Plone caches each translation catalog it sends to the browser.
Ask the first instance for the English catalog:

```shell
curl "http://localhost:8080/Plone/plonejsi18n?domain=plone&language=en"
```

You see a long JSON object of translations.

Now look at the first instance's status:

```shell
curl -u admin:admin -H "Accept: application/json" http://localhost:8080/Plone/@redismemoize
```

Find `plone.app.content.browser.i18n._gettext_catalog` under `functions`.
Its route is `redis`, and its counters show one `redis_misses`: the instance did not find the catalog in Redis, computed it, and stored it there.

## Read it on the second instance

Ask the second instance for the same catalog:

```shell
curl "http://localhost:8081/Plone/plonejsi18n?domain=plone&language=en"
```

Look at the second instance's status:

```shell
curl -u admin:admin -H "Accept: application/json" http://localhost:8081/Plone/@redismemoize
```

This time, the counters of `plone.app.content.browser.i18n._gettext_catalog` show one `redis_hits` and no `redis_misses`.
The second instance never computed the catalog: it read the one the first instance stored.

Notice also `server`, with Redis's version, and `breaker`, with `open` set to `false`.

## Clean up

Stop both instances with {kbd}`Control-C`, then stop Redis:

```shell
docker stop redismemoize-tutorial
```

You have now shared a cached value between two Plone instances that share nothing else.

## Next steps

- {doc}`/how-to-guides/configure` shows how to set this up for a real deployment.
- {doc}`/concepts/what-shareable-means` explains which values go to Redis, and which stay in RAM.
