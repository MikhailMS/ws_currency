import logging

from dataclasses import dataclass, field
from datetime    import datetime,  timedelta
from functools   import reduce
from itertools   import groupby

@dataclass
class User:
    name:         str
    history:      dict  = field(default_factory = lambda: {'deposit': [], 'withdrawal': [],
                                                           'transfer': [Transfer(datetime.utcnow().strftime('%Y-%m-%d'), 0.0, 'open_acct'),
                                                                        Transfer(datetime.utcnow().strftime('%Y-%m-%d'), 0.0, 'open_acct')],
                                                           'balance': []})
    money_limit:  int   = 10000
    period_limit: int   = 5
    balance:      float = 0.0
    logger = logging.getLogger('User')

    def is_transfer_within_limit(self, amount) -> bool:
        current_withdraw = []
        today = datetime.utcnow().strftime('%Y-%m-%d')
        today = datetime.strptime(today, '%Y-%m-%d')
        limit_range_days = sorted([ f'{today - timedelta(day)}'[:10] for day in range(self.period_limit) ])
        self.logger.info(limit_range_days)

        sorted_transfers        = sorted(self.history['transfer'], key = lambda x: x.date)
        self.logger.info('Sorted transfers: {}'.format(sorted_transfers))
        grouped_transfers       = groupby(sorted_transfers, key = lambda x: x.date)
        self.logger.info('Grouped transfers: {}'.format(grouped_transfers))
        grouped_transfers       = [ tmp for tmp in grouped_transfers ]
        self.logger.info('Grouped transfers(list): {}'.format(grouped_transfers))
        recent_transfers_groups = grouped_transfers[-5:]
        self.logger.info('Recent transfers_groups: {}'.format(recent_transfers_groups))
        recent_groups_date      = [ tmp[0] for tmp in recent_transfers_groups ]
        self.logger.info('Dates of recent transfers groups: {}'.format(recent_groups_date))
        self.logger.info('Limit to dates: {}'.format(limit_range_days))

        if recent_groups_date == limit_range_days:
            self.logger.info(recent_transfers_groups)
            for lol in recent_transfers_groups:
                self.logger.info('Lol: {}'.format(lol))
                for t in lol[1]:
                    self.logger.info('Lol t: {}'.format(t))

            # all_recent_transfers = [ item for tmp in recent_transfers_groups for item in tmp[0] ]
            # self.logger.info('Checking limits for: {}'.format(all_recent_transfers))
            hit_limit = reduce(lambda x, y: x.amount + y.amount, all_recent_transfers)
            self.logger.info(hit_limit)

            if hit_limit + amount <= self.money_limit:
                return True
            return False

        return True

    def make_deposit(self, amount: float, date: str) -> dict:
        self.balance += amount
        self.history['deposit'].append(Deposit(date, amount))

        return {"method": "deposit", "status": "Success", "result": f"{self.name} deposited {amount } EUR"}

    def make_withdrawal(self, amount: float, date: str) -> dict:
        if amount > self.balance:
            return {"method": "withdrawal", "status": "Fail", "result": f"{self.name} has insufficient funds to withdraw {amount} EUR"}

        self.balance -= amount
        self.history['withdrawal'].append(Withdrawal(date, amount))
        return {"method": "withdrawal", "status": "Success", "result": f"{self.name} withdrew {amount} EUR"}

    def make_transfer(self, amount: str, to_user, date: str) -> dict:
        if amount > self.balance:
            return {"method": "transfer", "status": "Fail", "result": f"{self.name} has insufficient funds to transfer {amount} EUR"}
        if not self.is_transfer_within_limit(amount):
            return {"method": "transfer", "status": "Fail", "result": f"{self.name} has hit allowed transfer limit"}

        self.make_withdrawal(amount, date)
        to_user.make_deposit(amount, date)
        self.history['transfer'].append(Transfer(date, amount, to_user.name))
        return {"method": "transfer", "status": "Success", "result": f"{self.name} has transfered funds to {to_user.name}"}

    def get_balance(self, date: str) -> dict:
        self.history['deposit'].append(Balance(date))
        print (self.balance)
        return {"method": "get_balances", "status": "Success", "result": f"{self.name} has {self.balance} EUR available"}

@dataclass
class Deposit:
    date: str
    amount: float

@dataclass
class Withdrawal:
    date: str
    amount: float

@dataclass
class Transfer:
    date: str
    amount: float
    to_account: str

@dataclass
class Balance:
    date: str
