from typing      import List
from dataclasses import dataclass, field
from datetime    import datetime

@dataclass
class Currency:
    base_currency: str = 'EUR'
    date: str = datetime.utcnow().strftime('%Y-%m-%d')
    supported_currency: List[str] = field(default_factory = lambda: ['USD', 'GBP', 'EUR', 'JPY', 'RUB'])
    rates: dict = None

    def is_supported_currency(self, curr: str) -> bool:
        return curr in self.supported_currency

    def convert_to_base(self, amount: float, curr: str) -> float:
        if curr.upper() == self.base_currency:
            return amount
        ratio = float(self.rates[curr.upper()])
        return round((amount / ratio), 3)
