from dataclasses import dataclass, field
from typing import Dict
from datetime import datetime
import uuid


@dataclass
class CryptoSyntheticBalance:
    currency: str
    units: float = 0.0
    avg_purchase_price: float = 0.0
    current_value: float = 0.0

    def update_value(self, current_price: float):
        self.current_value = self.units * current_price


@dataclass
class SyntheticCryptoAccount:
    user_id: str
    account_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fiat_balance: float = 0.0
    crypto_balances: Dict[str, CryptoSyntheticBalance] = field(default_factory=dict)
    total_crypto_value: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        for crypto in ['BTC', 'ETH']:
            if crypto not in self.crypto_balances:
                self.crypto_balances[crypto] = CryptoSyntheticBalance(currency=crypto)

    def update_portfolio_value(self, price_feed: Dict[str, float]):
        total = 0.0
        for crypto, balance in self.crypto_balances.items():
            if crypto in price_feed:
                balance.update_value(price_feed[crypto])
                total += balance.current_value
        self.total_crypto_value = total
        self.last_updated = datetime.now()

    def get_portfolio_overview(self) -> Dict:
        return {
            'user_id': self.user_id,
            'fiat_balance': self.fiat_balance,
            'total_crypto_value': self.total_crypto_value,
            'crypto_allocations': {
                crypto: {
                    'units': balance.units,
                    'current_value': balance.current_value,
                    'avg_price': balance.avg_purchase_price
                }
                for crypto, balance in self.crypto_balances.items()
            }
        }