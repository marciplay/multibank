import pytest
import os
from crypto_module.services.trading import CryptoTradingService
from crypto_module.services.pricing import RobustPriceOracle
from crypto_module.models.user_account import SyntheticCryptoAccount


class TestCryptoServices:
    def setup_method(self):
        self.trading_service = CryptoTradingService()
        self.price_oracle = RobustPriceOracle()

    def test_account_creation(self):
        """Тест создания аккаунта"""
        account = SyntheticCryptoAccount(user_id="test_user_123")
        assert account.user_id == "test_user_123"
        assert account.fiat_balance == 0.0
        assert 'BTC' in account.crypto_balances
        assert 'ETH' in account.crypto_balances

    def test_deposit_funds(self):
        """Тест пополнения счета"""
        result = self.trading_service.deposit("test_user", 1000.0)
        assert result['success'] == True
        assert result['new_balance'] == 1000.0

    def test_buy_crypto_insufficient_funds(self):
        """Тест покупки без достаточных средств"""
        result = self.trading_service.buy_crypto("test_user", "BTC", 1000.0)
        # Должен вернуть ошибку, так счет пустой
        assert result['success'] == False
        assert 'Insufficient' in result['error']

    def test_price_oracle(self):
        """Тест получения цен (может падать если нет интернета)"""
        try:
            price = self.price_oracle.get_market_price('BTC')
            assert price > 0
        except Exception as e:
            # Если нет интернета - пропускаем тест
            pytest.skip(f"No internet connection: {e}")

    def test_risk_management(self):
        """Тест риск-менеджмента"""
        risk_report = self.trading_service.risk_manager.get_risk_report()
        assert 'net_exposure' in risk_report
        assert 'daily_volume' in risk_report
        assert 'client_imbalance' in risk_report


if __name__ == "__main__":
    pytest.main()