import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CryptoConfig:
    # Основные настройки
    SUPPORTED_CRYPTOS: List[str] = None
    BASE_SPREAD: float = 0.02  # 2% базовый спред
    MAX_CLIENT_BALANCE: float = 10000.0  # $10K лимит на клиента
    AUTO_HEDGE_THRESHOLD: float = 50000.0  # $50K порог хеджирования

    # Настройки рисков
    RISK_LIMITS: Dict[str, float] = None
    VOLATILITY_ADJUSTMENT: bool = True

    # Лимиты платежей
    MAX_DEPOSIT_AMOUNT: float = 50000.0
    MAX_WITHDRAWAL_AMOUNT: float = 25000.0

    # API ключи (в проде хранить в vault)
    EXCHANGE_APIS: Dict = None

    def __post_init__(self):
        if self.SUPPORTED_CRYPTOS is None:
            self.SUPPORTED_CRYPTOS = ['BTC', 'ETH', 'USDT', 'BNB']

        if self.RISK_LIMITS is None:
            self.RISK_LIMITS = {
                'max_net_exposure': 100000.0,
                'max_daily_volume': 5000000.0,
                'var_95_limit': 250000.0
            }

        if self.EXCHANGE_APIS is None:
            self.EXCHANGE_APIS = {
                'binance': os.getenv('BINANCE_API_KEY', ''),
                'coinbase': os.getenv('COINBASE_API_KEY', '')
            }


# Глобальная конфигурация
config = CryptoConfig()