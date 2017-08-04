import functools
from random import random
import logging

import click
import aioredis
from aiohttp import web


types = {'version', 'group', 'user'}
global_type = 'global'
sep = ':'


def validate_params(func):
    @functools.wraps(func)
    async def wrapped(request):
        params = request.query
        if set(params.keys()) - types:
            msg = 'invalid parameters'
            return web.json_response({'error': msg}, status=401)
        return await func(request)
    return wrapped


def join(*values):
    return sep.join(values)


async def get_tags(redis, **identifiers):
    # keys for redis sets represending each identifier e.g. `user:foo`
    identifier_keys = [join(k, v) for k, v in identifiers.items()]

    # a random token to use as a suffix for our 2 temp keys,
    # used to store the results of 2 set union operations.
    token = str(random())

    # the 2 temp keys
    store_pos = join('calculated', 'positive', token)
    store_neg = join('calculated', 'negative', token)

    # temporarily store the result of unioning all members
    # of all 'positive' sets for all identifiers.
    await redis.sunionstore(
        store_pos,
        join('positive', global_type),
        *[join('positive', p) for p in identifier_keys])

    # temporarily store the result of unioning all members
    # of all 'negative' sets for all identifiers.
    await redis.sunionstore(
        store_neg,
        join('negative', global_type),
        *[join('negative', p) for p in identifier_keys])

    # subtract the negative calculated set from the positive and return.
    result = await redis.sdiff(store_pos, store_neg)

    # delete the temp keys.
    await redis.delete(store_pos, store_neg)

    # return result as a list of `str` objects.
    return [v.decode() for v in result]


@validate_params
async def handle(request):
    redis = request.app['redis']
    tags = await get_tags(redis, **request.query)
    return web.json_response(dict(features=tags))


async def attach_redis(app):
    app['redis'] = await aioredis.create_redis(
        (app.options['redis_host'], app.options['redis_port']),
        loop=app.loop)


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
def main(**options):
    logging.basicConfig(level=getattr(logging, options['loglevel'].upper()))

    app = web.Application()
    app.router.add_get('/', handle)
    app.options = options
    app.on_startup.append(attach_redis)
    app.on_cleanup.append(cleanup_redis)

    web.run_app(app, host=options['host'], port=options['port'])


if __name__ == '__main__':
    main()
