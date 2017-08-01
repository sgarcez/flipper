
from setuptools import setup

name = 'Flipper'
version = '0.1.1dev'

requires = [
    'aiohttp',
    'aioredis',
    'click',
]

tests_requires = [
    'pytest',
]


develop_requires = tests_requires + [
    'ipython',
    'ipdb',
    'flake8'
]

setup(
    name=name,
    version=version,
    py_modules=['flipper'],
    install_requires=requires,
    extras_require={
        'dev': develop_requires,
        'test': tests_requires,
    },
    entry_points="""\
        [console_scripts]
        flipper-server = flipper:main
    """,
)
