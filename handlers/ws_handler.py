from aiohttp     import WSMsgType, ClientSession
from aiohttp.web import WebSocketResponse

from models import Currency, User
from utils  import registry

class Handler():

    ENDPOINT = '/bank'

    @registry.register_get(ENDPOINT, atomic = True)
    async def websocket_handler(request, app = None) -> WebSocketResponse:
        async def helper(app, msg):
            json_msg = msg.json()
            method   = json_msg['method']
            func     = Helpers.supported_operations.get(method, None)
            if func:
                response = await func(app, json_msg)
                await ws.send_json(response)
            else:
                await ws.send_json({"error": f"{method} is unsupported method"})

        ws = WebSocketResponse()
        await ws.prepare(request)

        app.logger.info('WS connection is opened')
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data.strip() == 'close':
                    await ws.close()
                else:
                    if await app.is_currency_state_valid():
                        await helper(app, msg)
                    else:
                        await Helpers.call_exchange(app)
                        await helper(app, msg)


            elif msg.type == WSMsgType.ERROR:
                app.logger.info(f'WS connection closed with exception {ws.exception()}')

        app.logger.info('WS connection closed')
        return ws


class Helpers():

    @staticmethod
    async def call_exchange(app) -> dict:
        async with ClientSession() as session:
            async with session.get('https://api.exchangeratesapi.io/latest') as resp:
                json_response = await resp.json()

                date               = json_response['date']
                rates              = json_response['rates']
                app.currency_state = Currency(date = date, rates = rates)

    @staticmethod
    async def call_deposit(app, request: dict) -> dict:
        app.logger.info('User made deposit')
        user       = request['account']
        amount     = request['amt']
        currency   = request['ccy']
        date       = request['date']
        user_class = app.users.get(user, None)

        if app.currency_state.is_supported_currency(currency):
            amount = app.currency_state.convert_to_base(amount, currency)
        else:
            return {"error": f"{currency.upper()} currency is not supported at the moment"}

        if user_class:
            return user_class.make_deposit(amount, date)

        new_user        = User(user)
        app.users[user] = new_user
        return new_user.make_deposit(amount, date)


    @staticmethod
    async def call_withdrawal(app, request: dict) -> dict:
        app.logger.info('User requested withdrawal')
        user       = request['account']
        amount     = request['amt']
        currency   = request['ccy']
        date       = request['date']
        user_class = app.users.get(user, None)

        if app.currency_state.is_supported_currency(currency):
            amount = app.currency_state.convert_to_base(amount, currency)
        else:
            return {"error": f"{currency.upper()} currency is not supported at the moment"}

        if user_class:
            return user_class.make_withdrawal(amount, date)
        else:
            app.logger.warning('Cannot perform withdrawal from non-existing account')
            return {"error": "Cannot perform withdrawal from non-existing account"}

    @staticmethod
    async def call_transfer(app, request: dict) -> dict:
        app.logger.info('User requested transfer')
        from_user = request['from_account']
        to_user   = request['to_account']
        amount    = request['amt']
        currency  = request['ccy']
        date      = request['date']

        if app.currency_state.is_supported_currency(currency):
            amount = app.currency_state.convert_to_base(amount, currency)
        else:
            return {"error": f"{currency.upper()} currency is not supported at the moment"}

        from_user_class = app.users.get(from_user, None)
        to_user_class   = app.users.get(to_user, None)

        if from_user_class and to_user_class:
            return from_user_class.make_transfer(amount, to_user_class, date)
        else:
            app.logger.warning('Cannot perform transfer from or to non-existing account')
            return {"error": "Cannot perform transfer from or to non-existing account"}

    @staticmethod
    async def call_get_balance(app, request: dict) -> dict:
        app.logger.info('User requested balance')
        user       = request['account']
        date       = request['date']
        user_class = app.users.get(user, None)

        if user_class:
            return user_class.get_balance(date)

        new_user        = User(user)
        app.users[user] = new_user
        return new_user.get_balance(date)

Helpers.supported_operations = {
    'deposit':     Helpers.call_deposit,
    'withdrawal':  Helpers.call_withdrawal,
    'transfer':    Helpers.call_transfer,
    'get_balances': Helpers.call_get_balance
}
