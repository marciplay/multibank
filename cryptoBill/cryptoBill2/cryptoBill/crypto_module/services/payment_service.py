import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import uuid
from ..models.transaction import Transaction, TransactionType, TransactionStatus
from ..config.settings import config

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, trading_service):
        self.trading_service = trading_service
        self.pending_transactions: Dict[str, Transaction] = {}

    def deposit_funds(self, user_id: str, amount: float, payment_method: str = "bank_transfer") -> Dict:
        """Ввод средств на крипто-счет"""
        try:
            if amount <= 0:
                return {'success': False, 'error': 'Amount must be positive'}

            if amount > config.MAX_DEPOSIT_AMOUNT:
                return {'success': False, 'error': f'Maximum deposit amount is ${config.MAX_DEPOSIT_AMOUNT}'}

            transaction = Transaction(
                transaction_id=str(uuid.uuid4()),
                user_id=user_id,
                type=TransactionType.DEPOSIT,
                amount=amount,
                currency="USD",
                status=TransactionStatus.PENDING,
                created_at=datetime.now(),
                description=f"Deposit via {payment_method}"
            )

            # Имитация обработки платежа
            self._process_payment_gateway(amount, payment_method)

            account = self.trading_service._get_user_account(user_id)
            account.fiat_balance += amount

            transaction.complete()
            self.pending_transactions[transaction.transaction_id] = transaction

            self.trading_service._save_account(user_id)

            logger.info(f"Deposit completed for {user_id}: ${amount:.2f}")

            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'new_balance': account.fiat_balance,
                'transaction': transaction
            }

        except Exception as e:
            logger.error(f"Deposit failed for {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    def withdraw_funds(self, user_id: str, amount: float, destination: str = "bank_account") -> Dict:
        """Вывод средств с крипто-счета"""
        try:
            if amount <= 0:
                return {'success': False, 'error': 'Amount must be positive'}

            if amount > config.MAX_WITHDRAWAL_AMOUNT:
                return {'success': False, 'error': f'Maximum withdrawal amount is ${config.MAX_WITHDRAWAL_AMOUNT}'}

            account = self.trading_service._get_user_account(user_id)

            if account.fiat_balance < amount:
                return {'success': False, 'error': 'Insufficient funds'}

            transaction = Transaction(
                transaction_id=str(uuid.uuid4()),
                user_id=user_id,
                type=TransactionType.WITHDRAWAL,
                amount=amount,
                currency="USD",
                status=TransactionStatus.PENDING,
                created_at=datetime.now(),
                description=f"Withdrawal to {destination}"
            )

            risk_check = self._check_withdrawal_risk(user_id, amount)
            if not risk_check['allowed']:
                return {'success': False, 'error': risk_check['reason']}

            account.fiat_balance -= amount
            self._process_withdrawal_gateway(amount, destination)

            transaction.complete()
            self.pending_transactions[transaction.transaction_id] = transaction

            self.trading_service._save_account(user_id)

            logger.info(f"Withdrawal completed for {user_id}: ${amount:.2f}")

            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'new_balance': account.fiat_balance,
                'estimated_arrival': '1-3 business days',
                'transaction': transaction
            }

        except Exception as e:
            logger.error(f"Withdrawal failed for {user_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_transaction_history(self, user_id: str, limit: int = 50) -> List[Transaction]:
        """История транзакций пользователя"""
        user_transactions = [
            tx for tx in self.pending_transactions.values()
            if tx.user_id == user_id
        ]
        return sorted(user_transactions, key=lambda x: x.created_at, reverse=True)[:limit]

    def _process_payment_gateway(self, amount: float, payment_method: str):
        """Интеграция с платежными системами (заглушка)"""
        logger.info(f"Processing payment: ${amount} via {payment_method}")

    def _process_withdrawal_gateway(self, amount: float, destination: str):
        """Обработка вывода средств (заглушка)"""
        logger.info(f"Processing withdrawal: ${amount} to {destination}")

    def _check_withdrawal_risk(self, user_id: str, amount: float) -> Dict:
        """Проверка рисков при выводе"""
        if amount > 10000:
            return {
                'allowed': False,
                'reason': 'Large withdrawal requires manual verification'
            }

        recent_withdrawals = self._get_recent_withdrawals(user_id)
        if len(recent_withdrawals) > 5:
            return {
                'allowed': False,
                'reason': 'Too many recent withdrawals'
            }

        return {'allowed': True}

    def _get_recent_withdrawals(self, user_id: str) -> List[Transaction]:
        """Получает recent withdrawals пользователя"""
        user_txs = self.get_transaction_history(user_id, limit=100)
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

        return [
            tx for tx in user_txs
            if tx.type == TransactionType.WITHDRAWAL
               and tx.created_at > twenty_four_hours_ago
        ]