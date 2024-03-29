import aioredis
from functools import partial
import pytest
from flipper import get_tags, join


@pytest.fixture
async def redis(request, event_loop):
    redis = await aioredis.create_redis(
        ('localhost', 6379), db=2, loop=event_loop)
    await redis.flushdb()
    yield redis
    await redis.flushdb()
    redis.close()
    await redis.wait_closed()


@pytest.fixture
async def redis_script(redis, event_loop):
    with open('script.lua') as f:
        script = f.read()
    script_sha = await redis.script_load(script)
    return partial(redis.evalsha, script_sha)


@pytest.mark.asyncio
async def test_redis_access(redis, redis_script):
    res = await redis.sadd('test_set', 'member1')
    assert res == 1


async def create_tags(redis, tag_defs):
    for variant, tag_set in tag_defs.items():
        global_tags = tag_set.get('global_tags')
        if global_tags:
            await redis.sadd(join('global', variant), *global_tags)
        for typ, members in tag_set['tags'].items():
            for member, tags in members.items():
                if tags:
                    k = join(typ, member, variant)
                    await redis.sadd(k, *tags)


@pytest.mark.asyncio
async def test_empty(redis, redis_script):
    res = await get_tags(redis_script, user='u1', group='g1', version='v1')
    assert res == []


@pytest.mark.asyncio
async def test_tags_global_only(redis, redis_script):
    tag_defs = {
        'positive': {
            'global_tags': ['A', 'B'],
            'tags': {}
        },
        'negative': {
            'global_tags': ['A'],
            'tags': {}
        }
    }
    await create_tags(redis, tag_defs)

    res = await get_tags(redis_script, user='u1', group='g1', version='v1')
    assert set(res) == set(['B'])


@pytest.mark.asyncio
async def test_tags_no_overrides(redis, redis_script):
    tag_defs = {
        'positive': {
            'global_tags': ['A'],
            'tags': {
                'user': {
                    'u1': ['B', 'C']
                },
                'group': {
                    'g1': ['D', 'E']
                },
                'version': {
                    'v1': ['F', 'G']
                }
            }
        }
    }
    await create_tags(redis, tag_defs)

    res = await get_tags(redis_script, user='u1', group='g1', version='v1')
    assert set(res) == set(['A', 'B', 'C', 'D', 'E', 'F', 'G'])


@pytest.mark.asyncio
async def test_tags_user_override(redis, redis_script):
    tag_defs = {
        'positive': {
            'global_tags': ['A'],
            'tags': {
                'user': {
                    'u1': ['B', 'C']
                },
                'group': {
                    'g1': ['D', 'E']
                },
                'version': {
                    'v1': ['F', 'G']
                }
            }
        },
        'negative': {
            'tags': {
                'user': {
                    'u1': ['A']
                }
            }
        }
    }
    await create_tags(redis, tag_defs)

    res = await get_tags(redis_script, user='u1', group='g1', version='v1')
    assert set(res) == set(['B', 'C', 'D', 'E', 'F', 'G'])


@pytest.mark.asyncio
async def test_tags_user_group_override(redis, redis_script):
    tag_defs = {
        'positive': {
            'global_tags': ['A'],
            'tags': {
                'user': {
                    'u1': ['B', 'C']
                },
                'group': {
                    'g1': ['D', 'E']
                },
                'version': {
                    'v1': ['F', 'G']
                }
            }
        },
        'negative': {
            'tags': {
                'user': {
                    'u1': ['G']
                },
                'group': {
                    'g1': ['F']
                }
            }
        }
    }
    await create_tags(redis, tag_defs)

    res = await get_tags(redis_script, user='u1', group='g1', version='v1')
    assert set(res) == set(['A', 'B', 'C', 'D', 'E'])


@pytest.mark.asyncio
async def test_tags_version_override(redis, redis_script):
    tag_defs = {
        'positive': {
            'global_tags': ['A'],
            'tags': {
                'user': {
                    'u1': ['B', 'C']
                },
                'group': {
                    'g1': ['D', 'E']
                },
                'version': {
                    'v1': ['F', 'G']
                }
            }
        },
        'negative': {
            'tags': {
                'version': {
                    'v1': ['A', 'B', 'C']
                }
            }
        }
    }
    await create_tags(redis, tag_defs)

    res = await get_tags(redis_script, user='u1', group='g1', version='v1')
    assert set(res) == set(['D', 'E', 'F', 'G'])


@pytest.mark.asyncio
async def test_tags_multiple_overrides(redis, redis_script):
    tag_defs = {
        'positive': {
            'global_tags': ['A'],
            'tags': {
                'user': {
                    'u1': ['B', 'C']
                },
                'group': {
                    'g1': ['D', 'E']
                },
                'version': {
                    'v1': ['F', 'G']
                }
            }
        },
        'negative': {
            'global_tags': ['C'],
            'tags': {
                'group': {
                    'g1': ['D', 'E']
                },
                'version': {
                    'v1': ['A', 'B', 'C']
                }
            }
        }
    }
    await create_tags(redis, tag_defs)
    res = await get_tags(redis_script, user='u1', group='g1', version='v1')
    assert set(res) == set(['F', 'G'])


@pytest.mark.asyncio
async def test_tags_multiple_members_overrides(redis, redis_script):
    tag_defs = {
        'positive': {
            'global_tags': ['A'],
            'tags': {
                'user': {
                    'u1': ['B'],
                    'u2': ['C']
                },
                'group': {
                    'g1': ['D'],
                    'g2': ['E']
                },
                'version': {
                    'v1': ['F'],
                    'v2': ['G']
                }
            }
        },
        'negative': {
            'global_tags': ['A'],
            'tags': {
                'group': {
                    'g1': ['B'],
                    'g2': ['E'],
                },
                'version': {
                    'v2': ['G']
                }
            }
        }
    }
    await create_tags(redis, tag_defs)
    res = await get_tags(redis_script, user='u1', group='g1', version='v1')
    assert set(res) == set(['D', 'F'])
    res = await get_tags(redis_script, user='u2', group='g2', version='v2')
    assert set(res) == set(['C'])
