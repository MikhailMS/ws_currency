import logging

from dataclasses import dataclass, field
from datetime    import datetime,  timedelta
from functools   import reduce
from itertools   import groupby

@dataclass
class User:
    name:         str
    history:      dict  = field(default_factory = lambda: {'deposit': [], 'withdrawal': [],
                                                           'transfer': [],
                                                           'balance': []})
    money_limit:  int   = 10000
    period_limit: int   = 5
    balance:      float = 0.0
    logger = logging.getLogger('User')

    def is_transfer_within_limit(self, amount, date) -> bool:
        current_withdraw = []
        today            = datetime.utcnow().strftime('%Y-%m-%d')
        today            = datetime.strptime(today, '%Y-%m-%d')
        limit_range_days = sorted([ f'{today - timedelta(day)}'[:10] for day in range(self.period_limit) ])

        transfers  = self.history['transfer']
        grouped_transfers = groupby(transfers, key = lambda x: x.date)
        grouped_dict      = dict()
        for tmp in grouped_transfers:
            grouped_dict[tmp[0]] = [ t for t in tmp[1] ]

        recent_keys = sorted(grouped_dict.keys())[-5:]

        # Find if days are consecutive
        recent_dates = [datetime.strptime(d, '%Y-%m-%d') for d in recent_keys]
        if recent_dates:
            recent_dates.append(datetime.strptime(date, '%Y-%m-%d'))
        else:
            recent_dates = [datetime.strptime(date, '%Y-%m-%d')]

        date_ints    = set([d.toordinal() for d in recent_dates])

        print (date_ints)

        if date_ints:
            is_consecutive = (max(date_ints) - min(date_ints)) == (len(date_ints) - 1)
        else:
            is_consecutive = False

        # Check for money limit
        gained_limit = 0
        for date, transfers in grouped_dict.items():
            if date in limit_range_days:
                self.logger.info(transfers)
                for transfer in transfers:
                    gained_limit += transfer.amount
        self.logger.info('Gained limit: {}, is consecutive? {}'.format(gained_limit, is_consecutive))

        transfer_not_allowed = gained_limit + amount > self.money_limit and is_consecutive
        self.logger.info('Do not allow transfer? {}'.format(transfer_not_allowed))

        return not transfer_not_allowed

    def make_deposit(self, amount: float, date: str) -> dict:
        self.balance += amount
        self.history['deposit'].append(Deposit(date, amount))

        return {"method": "deposit", "status": "Success",
                "result": f"{self.name} deposited {amount } EUR"}

    def make_withdrawal(self, amount: float, date: str) -> dict:
        if amount > self.balance:
            return {"method": "withdrawal", "status": "Fail",
                    "result": f"{self.name} has insufficient funds to withdraw {amount} EUR"}

        self.balance -= amount
        self.history['withdrawal'].append(Withdrawal(date, amount))
        return {"method": "withdrawal", "status": "Success",
                "result": f"{self.name} withdrew {amount} EUR"}

    def make_transfer(self, amount: str, to_user, date: str) -> dict:
        if amount > self.balance:
            return {"method": "transfer", "status": "Fail",
                    "result": f"{self.name} has insufficient funds to transfer {amount} EUR"}
        if not self.is_transfer_within_limit(amount, date):
            return {"method": "transfer", "status": "Fail",
                    "result": f"{self.name} has hit allowed transfer limit"}

        self.make_withdrawal(amount, date)
        to_user.make_deposit(amount, date)
        self.history['transfer'].append(Transfer(date, amount, to_user.name))
        return {"method": "transfer", "status": "Success",
                "result": f"{self.name} has transfered funds to {to_user.name}"}

    def get_balance(self, date: str) -> dict:
        self.history['deposit'].append(Balance(date))
        return {"method": "get_balances", "status": "Success",
                "result": f"{self.name} has {self.balance} EUR available"}

@dataclass
class Deposit:
    date:   str
    amount: float

@dataclass
class Withdrawal:
    date:   str
    amount: float

@dataclass
class Transfer:
    date:       str
    amount:     float
    to_account: str

@dataclass
class Balance:
    date: str
