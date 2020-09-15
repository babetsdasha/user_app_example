import asyncio
import importlib
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web
from cassandra.cluster import Cluster, NoHostAvailable
from cassandra.cqlengine import connection
from cassandra.cqlengine.management import create_keyspace_simple, sync_table

from users_app.middlewares import api_exception_middleware, logger_handler
from users_app.models import User
from users_app.routes import setup_routes

loop = asyncio.get_event_loop()
executor = ThreadPoolExecutor()

loop.set_default_executor(executor)

app = web.Application(loop=loop, middlewares=[logger_handler,
                                              api_exception_middleware])


async def init_log_session():
    pass


async def connect_to_cassandra(app):
    config = app['config']
    sleep = config.get('sleep', 0)
    max_retry = config.get('max_retry', 3)

    for i in range(max_retry):
        try:
            session = Cluster(config['cassandra_host']).connect()
        except NoHostAvailable:
            if i == (max_retry - 1):
                msg = (
                    'Failed to connect to cassandra, retrying '
                    'in %ss (%s/%s)'
                )
                await app['logger'].error('main.connect_to_cassndra',
                                          msg % (sleep, i + 1, max_retry))
                raise
            else:
                msg = (
                    'Failed to connect to cassandra, retrying '
                    'in %ss (%s/%s)'
                )
                await app['logger'].debug('main.connect_to_cassndra',
                                          msg % (sleep, i + 1, max_retry))
                time.sleep(sleep)

    connection.register_connection(
        config['default_connection'],
        session=session
    )
    create_keyspace_simple(
        config['default_keyspace'],
        replication_factor=1,
        connections=[config['default_connection']]
    )

    User.__keyspace__ = config['default_keyspace']
    User.__connection__ = config['default_connection']
    sync_table(
        User,
        keyspaces=[config['default_keyspace']],
        connections=[config['default_connection']]
    )


try:
    os.environ.setdefault('SETTINGS_MODULE', 'users_app.config')
    settings_module = importlib.import_module(os.environ['SETTINGS_MODULE'])

    app['config'] = {
        key: getattr(settings_module, key)
        for key in dir(settings_module)
        if not key.startswith('_')
    }
except ImportError:
    loop.run_until_complite(
        app['logger'].critical('main', 'Failed to read config!')
    )
    sys.exit(1)


async def start_background_tasks(app):
    app['logger'] = await init_log_session()
    app['connect_to_cassandra'] = app.loop.create_task(
        connect_to_cassandra(app)
    )


async def cleanup_background_tasks(app):
    app['connect_to_cassandra'].cancel()
    await app['connect_to_cassandra']


app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)
setup_routes(app)

web.run_app(app, port=8000)
