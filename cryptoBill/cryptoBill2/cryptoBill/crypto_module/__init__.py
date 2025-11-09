"""
Модуль синтетической криптовалюты для мультибанка
"""

from .models.user_account import SyntheticCryptoAccount, CryptoSyntheticBalance
from .models.transaction import Transaction, TransactionType, TransactionStatus
from .services.trading import CryptoTradingService
from .services.pricing import RealTimePriceOracle
from .services.risk_manager import RiskManager
from .services.hedging import HedgingService
from .services.payment_service import PaymentService
from .services.storage import AccountStorage
from .config.settings import config, CryptoConfig
from .api.routes import router

__version__ = "1.0.0"
__author__ = "Мультибанк Команда"

__all__ = [
    'SyntheticCryptoAccount',
    'CryptoSyntheticBalance',
    'Transaction',
    'TransactionType',
    'TransactionStatus',
    'CryptoTradingService',
    'RobustPriceOracle',
    'RiskManager',
    'HedgingService',
    'PaymentService',
    'AccountStorage',
    'config',
    'CryptoConfig',
    'router'
]