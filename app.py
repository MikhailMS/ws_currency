import logging

from aiohttp  import web
from datetime import datetime

from models import Currency

class App():

    def __init__(self):
        self.app            = web.Application()
        self.logger         = logging.getLogger(self.__class__.__name__)
        self.users          = dict()
        self.currency_state = None

    def add_routes_from_registry(self, registry) -> None:
        for key, route_wrapper in registry.PLUGINS.items():
            method, endpoint = key.split(',')
            self.app.add_routes([web.get(endpoint, route_wrapper['func'])])

    async def is_currency_state_valid(self) -> bool:
        if self.currency_state:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            spin = (datetime.strptime(self.currency_state.date, '%Y-%m-%d') - datetime.strptime(today, '%Y-%m-%d')).days
            return True if spin == 0 else False
        return False
