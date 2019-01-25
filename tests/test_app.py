import pytest
import sys

from aiohttp         import ClientSession
from aiojobs.aiohttp import setup as setup_jobs
from datetime        import datetime, timedelta
from os              import getcwd
from os.path         import dirname, normpath, realpath, join, expanduser

PACKAGE_PARENT = '..'
SCRIPT_DIR     = dirname(realpath(join(getcwd(), expanduser(__file__))))
sys.path.append(normpath(join(SCRIPT_DIR, PACKAGE_PARENT)))

from app      import App
from utils    import registry
from handlers import WSHandler

def generate_dates():
    today          = datetime.utcnow().strftime('%Y-%m-%d')
    today          = datetime.strptime(today, '%Y-%m-%d')
    return sorted([ f'{today - timedelta(day)}'[:10] for day in range(5) ])

async def call_ws(loop, data, expected = None):
    session = ClientSession(loop = loop)
    async with session.ws_connect('http://localhost:5000/bank') as websocket:
        await websocket.send_json(data)
        response = await websocket.receive_json()

        print ('resp', response, type(response))
        if expected:
            print ('exp', expected, type(expected))
            assert response == expected

    await session.close()

@pytest.fixture
def setup(loop, aiohttp_server):
    app_wrapper = App()

    registry.set_app(app_wrapper)
    app_wrapper.add_routes_from_registry(registry)

    setup_jobs(app_wrapper.app)

    return loop.run_until_complete(aiohttp_server(app_wrapper.app, port = 5000)), loop

def test_deposit(setup):
    _, loop = setup

    data     = {"method": "deposit", "date": "2018-10-09",
                "account": "jack", "amt" : 100, "ccy": "EUR"}
    expected = {"method": "deposit", "status": "Success",
                "result": "jack deposited 100 EUR"}
    loop.run_until_complete(call_ws(loop, data, expected))

    data     = {"method": "get_balances", "date": "2018-10-09",
                "account": "jack"}
    expected = {"method": "get_balances", "status": "Success",
                "result": "jack has 100.0 EUR available"}
    loop.run_until_complete(call_ws(loop, data, expected))

def test_withdraw(setup):
    _, loop = setup

    # Withdraw test
    data = {"method": "deposit", "date": "2018-10-09",
            "account": "peter", "amt" : 100, "ccy": "EUR"}
    loop.run_until_complete(call_ws(loop, data))

    data     = {"method": "withdrawal", "date": "2018-10-09",
                "account": "peter", "amt" : 100, "ccy": "EUR"}
    expected = {"method": "withdrawal", "status": "Success",
                "result": "peter withdrew 100 EUR"}
    loop.run_until_complete(call_ws(loop, data, expected))

    data     = {"method": "get_balances", "date": "2018-10-09",
                "account": "peter"}
    expected = {"method": "get_balances", "status": "Success",
                "result": "peter has 0.0 EUR available"}
    loop.run_until_complete(call_ws(loop, data, expected))

def test_invalid_withdraw(setup):
    _, loop = setup

    # Invalid withdraw
    data = {"method": "deposit", "date": "2018-10-09",
            "account": "steve", "amt" : 100, "ccy": "EUR"}
    loop.run_until_complete(call_ws(loop, data))

    data     = {"method": "withdrawal", "date": "2018-10-09",
                "account": "steve", "amt" : 110, "ccy": "EUR"}
    expected = {"method": "withdrawal", "status": "Fail",
                "result": "steve has insufficient funds to withdraw 110 EUR"}
    loop.run_until_complete(call_ws(loop, data, expected))

def test_invalid_currency(setup):
    _, loop = setup

    # Invalid currency
    data     = {"method": "deposit", "date": "2018-10-09",
                "account": "bob", "amt" : 110, "ccy": "HUF"}
    expected = {"error": "HUF currency is not supported at the moment"}
    loop.run_until_complete(call_ws(loop, data, expected))

def test_invalid_transfer_limit_5_days(setup):
    # Prepare case
    _, loop        = setup
    cons_five_days = generate_dates()

    # Invalid transfer(limit hit in 5 days)
    data = {"method": "deposit", "date": "2018-10-09",
            "account": "bob", "amt" : 15000, "ccy": "EUR"}
    loop.run_until_complete(call_ws(loop, data))
    data = {"method": "deposit", "date": "2018-10-09",
            "account": "alice", "amt" : 10, "ccy": "EUR"}
    loop.run_until_complete(call_ws(loop, data))

    data = {"method": "transfer", "date": f"{cons_five_days[0]}",
            "to_account": "alice", "from_account": "bob", "amt" : 2001, "ccy": "GBP"}
    loop.run_until_complete(call_ws(loop, data))
    data = {"method": "transfer", "date": f"{cons_five_days[1]}",
            "to_account": "alice", "from_account": "bob", "amt" : 1000, "ccy": "GBP"}
    loop.run_until_complete(call_ws(loop, data))
    data = {"method": "transfer", "date": f"{cons_five_days[2]}",
            "to_account": "alice", "from_account": "bob", "amt" : 1000, "ccy": "GBP"}
    loop.run_until_complete(call_ws(loop, data))
    data = {"method": "transfer", "date": f"{cons_five_days[3]}",
            "to_account": "alice", "from_account": "bob", "amt" : 1000, "ccy": "GBP"}
    loop.run_until_complete(call_ws(loop, data))

    data = {"method": "transfer", "date": f"{cons_five_days[4]}",
            "to_account": "alice", "from_account": "bob", "amt" : 5000, "ccy": "GBP"}
    expected = {"method": "transfer", "status": "Fail",
                "result": "bob has hit allowed transfer limit"}
    loop.run_until_complete(call_ws(loop, data, expected))

def test_invalid_transfer_limit_less_5_days(setup):
    # Prepare case
    _, loop = setup
    cons_five_days = generate_dates()

    # Invalid transfer(limit hit in less than 5 days)
    data = {"method": "deposit", "date": "2018-10-09",
            "account": "alex", "amt" : 15000, "ccy": "EUR"}
    loop.run_until_complete(call_ws(loop, data))
    data = {"method": "deposit", "date": "2018-10-09",
            "account": "jane", "amt" : 10, "ccy": "EUR"}
    loop.run_until_complete(call_ws(loop, data))

    data = {"method": "transfer", "date": f"{cons_five_days[0]}",
            "to_account": "jane", "from_account": "alex", "amt" : 2001, "ccy": "GBP"}
    loop.run_until_complete(call_ws(loop, data))
    data = {"method": "transfer", "date": f"{cons_five_days[1]}",
            "to_account": "jane", "from_account": "alex", "amt" : 5000, "ccy": "GBP"}
    loop.run_until_complete(call_ws(loop, data))

    data = {"method": "transfer", "date": f"{cons_five_days[2]}",
            "to_account": "jane", "from_account": "alex", "amt" : 3000, "ccy": "GBP"}
    expected = {"method": "transfer", "status": "Fail",
                "result": "alex has hit allowed transfer limit"}
    loop.run_until_complete(call_ws(loop, data, expected))

def test_valid_transfer(setup):
    # Prepare case
    _, loop = setup
    cons_five_days = generate_dates()

    # # Valid transfer(limit is not hit, because consecutive rule is not breached)
    data = {"method": "deposit", "date": "2018-10-09",
            "account": "felix", "amt" : 15000, "ccy": "EUR"}
    loop.run_until_complete(call_ws(loop, data))
    data = {"method": "deposit", "date": "2018-10-09",
            "account": "jasmine", "amt" : 10, "ccy": "EUR"}
    loop.run_until_complete(call_ws(loop, data))

    data = {"method": "transfer", "date": f"{cons_five_days[0]}",
            "to_account": "jasmine", "from_account": "felix", "amt" : 2001, "ccy": "GBP"}
    loop.run_until_complete(call_ws(loop, data))
    data = {"method": "transfer", "date": f"{cons_five_days[1]}",
            "to_account": "jasmine", "from_account": "felix", "amt" : 5000, "ccy": "GBP"}
    loop.run_until_complete(call_ws(loop, data))

    data = {"method": "transfer", "date": f"{cons_five_days[-1]}",
            "to_account": "jasmine", "from_account": "felix", "amt" : 3000, "ccy": "GBP"}
    expected = {"method": "transfer", "status": "Success",
                "result": "felix has transfered funds to jasmine"}
    loop.run_until_complete(call_ws(loop, data, expected))
