import logging

from aiojobs.aiohttp import setup
from aiohttp         import web

from app     import App
from utils    import registry
from handlers import WSHandler

logging.basicConfig(format = '%(levelname)s (%(funcName)s) in [%(name)s] @ [%(asctime)s] => %(message)s',
                    level = 'DEBUG')

app_wrapper = App()
registry.set_app(app_wrapper)
app_wrapper.add_routes_from_registry(registry)

setup(app_wrapper.app)

web.run_app(app_wrapper.app, host = 'localhost', port = '5000')
