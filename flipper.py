import functools
import base64
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


async def get_tags(redis, **kwargs):
    encoded_principals = [join(k, v) for k, v in kwargs.items()]
    canon_id = base64.b64encode(str(encoded_principals).encode()).decode()

    store_pos = join('calculated', 'positive', canon_id)
    store_neg = join('calculated', 'negative', canon_id)

    await redis.sunionstore(
        store_pos,
        join('positive', global_type),
        *[join('positive', p) for p in encoded_principals])

    await redis.sunionstore(
        store_neg,
        join('negative', global_type),
        *[join('negative', p) for p in encoded_principals])

    result = await redis.sdiff(store_pos, store_neg)

    await redis.delete(store_pos, store_neg)

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
@click.option('--redis-host', '-h', default="127.0.0.1")
@click.option('--redis-port', '-p', default=6379)
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
