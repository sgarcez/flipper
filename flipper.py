import functools
from random import random
from functools import partial
import logging

import click
import aioredis
from aiohttp import web


def validate_params(func):
    @functools.wraps(func)
    async def wrapped(request):
        params = request.query
        if set(params.keys()) - request.app.options['allowed_id_types']:
            msg = 'invalid parameters'
            return web.json_response({'error': msg}, status=401)
        return await func(request)
    return wrapped


def join(*values, sep=':'):
    return sep.join(values)


async def get_tags(redis_script, **identifiers):
    """Executes a lua script stored in redis that does all set operations.
    """

    # keys for redis sets represending each identifier e.g. `user:foo`
    identifier_keys = [join(k, v) for k, v in identifiers.items()]

    # cheap unique identifier for request
    token = random()

    result = await redis_script(identifier_keys, [token])

    # decode bytes since json encoder requires unicode strings
    return [i.decode() for i in result]


# @validate_params
async def handle(request):
    tags = await get_tags(request.app['redis_script'], **request.query)
    return web.json_response(dict(features=tags))


async def attach_redis(app):
    redis = await aioredis.create_redis(
        (app.options['redis_host'], app.options['redis_port']), loop=app.loop)
    with open(app.options['lua_script']) as f:
        script = f.read()
    script_sha = await redis.script_load(script)
    app['redis_script'] = partial(redis.evalsha, script_sha)
    app['redis'] = redis


async def cleanup_redis(app):
    redis = app['redis']
    redis.close()
    await redis.wait_closed()


@click.command()
@click.option('--loglevel', '-l', default="INFO", show_default=True)
@click.option('--host', '-h', default="127.0.0.1")
@click.option('--port', '-p', default=5000)
@click.option('--redis-host', default="127.0.0.1")
@click.option('--redis-port', default=6379)
@click.option('--lua-script', default='script.lua')
@click.option('--allowed-id-types', default='version,group,user')
def main(**options):
    logging.basicConfig(level=getattr(logging, options['loglevel'].upper()))

    app = web.Application()
    app.router.add_get('/', handle)
    app.options = options
    app.options['allowed_id_types'] = set(
        options['allowed_id_types'].split(','))
    app.on_startup.append(attach_redis)
    app.on_cleanup.append(cleanup_redis)

    web.run_app(app, host=options['host'], port=options['port'])


if __name__ == '__main__':
    main()
