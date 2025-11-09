from typing import Dict, Optional, List
import logging
from ..models.user_account import SyntheticCryptoAccount
from ..models.transaction import Transaction
from .pricing import RealTimePriceOracle
from .risk_manager import RiskManager
from .hedging import HedgingService
from .payment_service import PaymentService
from .storage import AccountStorage
from ..config.settings import config

logger = logging.getLogger(__name__)


class CryptoTradingService:
    def __init__(self):
        self.price_oracle = RealTimePriceOracle()
        self.risk_manager = RiskManager()
        self.hedging_service = HedgingService()
        self.storage = AccountStorage()
        self.payment_service = PaymentService(self)
        self.user_accounts: Dict[str, SyntheticCryptoAccount] = {}

    def deposit(self, user_id: str, amount: float, payment_method: str = "bank_transfer") -> Dict:
        return self.payment_service.deposit_funds(user_id, amount, payment_method)

    def withdraw(self, user_id: str, amount: float, destination: str = "bank_account") -> Dict:
        return self.payment_service.withdraw_funds(user_id, amount, destination)

    def get_transaction_history(self, user_id: str, limit: int = 50) -> List[Transaction]:
        return self.payment_service.get_transaction_history(user_id, limit)

    def buy_crypto(self, user_id: str, crypto: str, fiat_amount: float) -> Dict:
        try:
            if not self.risk_manager.check_trade_limits(user_id, fiat_amount, 'buy'):
                return {'success': False, 'error': 'Risk limits exceeded'}

            buy_price, sell_price, spread = self.price_oracle.calculate_spread(
                crypto, self.risk_manager.get_risk_report()['client_imbalance']
            )

            crypto_units = fiat_amount / buy_price
            account = self._get_user_account(user_id)

            if account.fiat_balance < fiat_amount:
                return {'success': False, 'error': 'Insufficient fiat balance'}

            account.fiat_balance -= fiat_amount
            crypto_balance = account.crypto_balances[crypto]

            if crypto_balance.units > 0:
                total_value = crypto_balance.units * crypto_balance.avg_purchase_price
                total_value += fiat_amount
                crypto_balance.units += crypto_units
                crypto_balance.avg_purchase_price = total_value / crypto_balance.units
            else:
                crypto_balance.units = crypto_units
                crypto_balance.avg_purchase_price = buy_price

            current_prices = {crypto: buy_price}
            account.update_portfolio_value(current_prices)
            self.risk_manager.update_metrics(user_id, fiat_amount, 'buy')
            self._check_and_execute_hedge()
            self._save_account(user_id)

            logger.info(f"BUY executed for {user_id}: {crypto_units:.6f} {crypto} for ${fiat_amount:.2f}")

            return {
                'success': True,
                'crypto_units': crypto_units,
                'price': buy_price,
                'total_cost': fiat_amount,
                'spread': spread,
                'new_balance': account.get_portfolio_overview()
            }

        except Exception as e:
            logger.error(f"Buy operation failed for {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    def sell_crypto(self, user_id: str, crypto: str, crypto_units: float) -> Dict:
        try:
            account = self._get_user_account(user_id)
            crypto_balance = account.crypto_balances.get(crypto)

            if not crypto_balance or crypto_balance.units < crypto_units:
                return {'success': False, 'error': 'Insufficient crypto balance'}

            buy_price, sell_price, spread = self.price_oracle.calculate_spread(
                crypto, self.risk_manager.get_risk_report()['client_imbalance']
            )

            fiat_amount = crypto_units * sell_price

            if not self.risk_manager.check_trade_limits(user_id, fiat_amount, 'sell'):
                return {'success': False, 'error': 'Risk limits exceeded'}

            crypto_balance.units -= crypto_units
            account.fiat_balance += fiat_amount

            current_prices = {crypto: sell_price}
            account.update_portfolio_value(current_prices)
            self.risk_manager.update_metrics(user_id, fiat_amount, 'sell')
            self._check_and_execute_hedge()
            self._save_account(user_id)

            logger.info(f"SELL executed for {user_id}: {crypto_units:.6f} {crypto} for ${fiat_amount:.2f}")

            return {
                'success': True,
                'fiat_amount': fiat_amount,
                'price': sell_price,
                'crypto_units': crypto_units,
                'spread': spread,
                'new_balance': account.get_portfolio_overview()
            }

        except Exception as e:
            logger.error(f"Sell operation failed for {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_portfolio(self, user_id: str) -> Optional[Dict]:
        account = self.user_accounts.get(user_id)
        if account:
            current_prices = {}
            for crypto in account.crypto_balances.keys():
                try:
                    current_prices[crypto] = self.price_oracle.get_market_price(crypto)
                except Exception as e:
                    logger.warning(f"Could not get price for {crypto}: {e}")
                    current_prices[crypto] = account.crypto_balances[crypto].avg_purchase_price

            account.update_portfolio_value(current_prices)
            return account.get_portfolio_overview()
        return None

    def _get_user_account(self, user_id: str) -> SyntheticCryptoAccount:
        if user_id not in self.user_accounts:
            account = self.storage.load_account(user_id)
            if account:
                self.user_accounts[user_id] = account
            else:
                self.user_accounts[user_id] = SyntheticCryptoAccount(user_id=user_id)
                self._save_account(user_id)

        return self.user_accounts[user_id]

    def _save_account(self, user_id: str):
        if user_id in self.user_accounts:
            try:
                self.storage.save_account(self.user_accounts[user_id])
            except Exception as e:
                logger.error(f"Failed to save account for {user_id}: {e}")

    def _check_and_execute_hedge(self):
        try:
            risk_report = self.risk_manager.get_risk_report()

            if abs(risk_report['net_exposure']) > config.AUTO_HEDGE_THRESHOLD:
                current_prices = {}
                for crypto in ['BTC', 'ETH']:
                    try:
                        current_prices[crypto] = self.price_oracle.get_market_price(crypto)
                    except Exception as e:
                        logger.warning(f"Could not get price for {crypto} for hedging: {e}")

                if current_prices:
                    hedge_needs = self.hedging_service.calculate_hedge_need(
                        risk_report['net_exposure'], current_prices
                    )
                    self.hedging_service.execute_hedge(hedge_needs, current_prices)
        except Exception as e:
            logger.error(f"Hedging check failed: {e}")

    def get_system_report(self) -> Dict:
        return {
            'risk_management': self.risk_manager.get_risk_report(),
            'hedging': self.hedging_service.get_hedge_report(),
            'total_users': len(self.user_accounts),
            'total_assets': sum(acc.total_crypto_value for acc in self.user_accounts.values()),
            'total_fiat': sum(acc.fiat_balance for acc in self.user_accounts.values())
        }

    def close_position(self, user_id: str, crypto: str) -> Dict:
        """Закрытие всей позиции по криптовалюте"""
        try:
            account = self._get_user_account(user_id)
            crypto_balance = account.crypto_balances.get(crypto)

            if not crypto_balance or crypto_balance.units <= 0:
                return {'success': False, 'error': f'No {crypto} position to close'}

            # Получаем текущую цену для продажи
            _, sell_price, spread = self.price_oracle.calculate_spread(crypto)

            # Продаем все единицы
            crypto_units = crypto_balance.units
            fiat_amount = crypto_units * sell_price

            # Выполняем продажу
            crypto_balance.units = 0
            account.fiat_balance += fiat_amount

            # Обновляем стоимость портфеля
            current_prices = {crypto: sell_price}
            account.update_portfolio_value(current_prices)

            # Обновляем метрики рисков
            self.risk_manager.update_metrics(user_id, fiat_amount, 'sell')

            # Проверяем хеджирование
            self._check_and_execute_hedge()

            # Сохраняем изменения
            self._save_account(user_id)

            logger.info(f"Position closed for {user_id}: {crypto_units:.6f} {crypto} for ${fiat_amount:.2f}")

            return {
                'success': True,
                'crypto_sold': crypto_units,
                'fiat_received': fiat_amount,
                'price': sell_price,
                'new_balance': account.get_portfolio_overview()
            }

        except Exception as e:
            logger.error(f"Close position failed for {user_id}: {e}")
            return {'success': False, 'error': str(e)}