import websockets
import asyncio

import pytest
import json

def test_app():
    # Deposit test
    data = {"method": "deposit", "date": "2018-10-09", "account": "bob", "amt" : 100, "ccy": "EUR"}
    expected = {"method": "deposit", "status": "Success", "result": "bob deposited 100 EUR"}
    asyncio.get_event_loop().run_until_complete(call_ws(data, expected))

    data = {"method": "get_balances", "date": "2018-10-09", "account": "bob"}
    expected = {"method": "get_balances", "status": "Success", "result": "bob has 100.0 EUR available"}
    asyncio.get_event_loop().run_until_complete(call_ws(data, expected))

    data = {"method": "deposit", "date": "2018-10-09", "account": "alice", "amt" : 100, "ccy": "EUR"}
    asyncio.get_event_loop().run_until_complete(call_ws(data))

    # Withdraw test
    data = {"method": "withdrawal", "date": "2018-10-09", "account": "bob", "amt" : 100, "ccy": "EUR"}
    expected = {"method": "withdrawal", "status": "Success", "result": "bob withdrew 100 EUR"}
    asyncio.get_event_loop().run_until_complete(call_ws(data, expected))

    data = {"method": "get_balances", "date": "2018-10-09", "account": "bob"}
    expected = {"method": "get_balances", "status": "Success", "result": "bob has 0.0 EUR available"}
    asyncio.get_event_loop().run_until_complete(call_ws(data, expected))

    # Invalid withdraw
    data = {"method": "deposit", "date": "2018-10-09", "account": "bob", "amt" : 100, "ccy": "EUR"}
    asyncio.get_event_loop().run_until_complete(call_ws(data))
    data = {"method": "withdrawal", "date": "2018-10-09", "account": "bob", "amt" : 110, "ccy": "EUR"}
    expected = {"method": "withdrawal", "status": "Fail", "result": "bob has insufficient funds to withdraw 110 EUR"}
    asyncio.get_event_loop().run_until_complete(call_ws(data, expected))

    # Invalid transfer(limit hit in 5 days)
    data = {"method": "deposit", "date": "2018-10-09", "account": "bob", "amt" : 15000, "ccy": "EUR"}
    asyncio.get_event_loop().run_until_complete(call_ws(data))

    data = {"method": "transfer", "date": "2019-01-09", "to_account": "alice", "from_account": "bob", "amt" : 2001, "ccy": "GBP"}
    asyncio.get_event_loop().run_until_complete(call_ws(data))
    data = {"method": "transfer", "date": "2019-01-10", "to_account": "alice", "from_account": "bob", "amt" : 1000, "ccy": "GBP"}
    asyncio.get_event_loop().run_until_complete(call_ws(data))
    data = {"method": "transfer", "date": "2019-01-11", "to_account": "alice", "from_account": "bob", "amt" : 1000, "ccy": "GBP"}
    asyncio.get_event_loop().run_until_complete(call_ws(data))
    data = {"method": "transfer", "date": "2019-01-12", "to_account": "alice", "from_account": "bob", "amt" : 1000, "ccy": "GBP"}
    asyncio.get_event_loop().run_until_complete(call_ws(data))
    data = {"method": "transfer", "date": "2019-01-13", "to_account": "alice", "from_account": "bob", "amt" : 5000, "ccy": "GBP"}
    expected = {"method": "transfer", "status": "Fail", "result": "bob has hit allowed transfer limit"}
    asyncio.get_event_loop().run_until_complete(call_ws(data, expected))

    # # Invalid transfer(limit hit in less than 5 days)
    # data = {"method": "deposit", "date": "2018-10-09", "account": "bob", "amt" : 15000, "ccy": "EUR"}
    # asyncio.get_event_loop().run_until_complete(call_ws(data))
    # data = {"method": "transfer", "date": "2019-01-09", "to_account": "alice", "from_account": "bob", "amt" : 2001, "ccy": "GBP"}
    # asyncio.get_event_loop().run_until_complete(call_ws(data))
    # data = {"method": "transfer", "date": "2019-01-10", "to_account": "alice", "from_account": "bob", "amt" : 5000, "ccy": "GBP"}
    # asyncio.get_event_loop().run_until_complete(call_ws(data))
    # data = {"method": "transfer", "date": "2019-01-11", "to_account": "alice", "from_account": "bob", "amt" : 3000, "ccy": "GBP"}
    # expected = {"method": "transfer", "status": "Fail", "result": "bob has hit allowed transfer limit"}
    # asyncio.get_event_loop().run_until_complete(call_ws(data, expected))

    # # Valid transfer(limit is not hit, because no consecutive rule is not breached)
    # data = {"method": "deposit", "date": "2018-10-09", "account": "bob", "amt" : 15000, "ccy": "EUR"}
    # asyncio.get_event_loop().run_until_complete(call_ws(data))
    # data = {"method": "transfer", "date": "2019-01-09", "to_account": "alice", "from_account": "bob", "amt" : 2001, "ccy": "GBP"}
    # asyncio.get_event_loop().run_until_complete(call_ws(data))
    # data = {"method": "transfer", "date": "2019-01-10", "to_account": "alice", "from_account": "bob", "amt" : 5000, "ccy": "GBP"}
    # asyncio.get_event_loop().run_until_complete(call_ws(data))
    # data = {"method": "transfer", "date": "2019-01-12", "to_account": "alice", "from_account": "bob", "amt" : 3000, "ccy": "GBP"}
    # expected = {"method": "transfer", "status": "Success", "result": "bob has transfered funds to alice"}
    # asyncio.get_event_loop().run_until_complete(call_ws(data, expected))


async def call_ws(data, expected = None):
    async with websockets.connect('ws://localhost:5000/bank') as websocket:
        await websocket.send(json.dumps(data))
        response = await websocket.recv()

        print (response)
        if expected:
            assert response == json.dumps(expected)
