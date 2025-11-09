import json
import sqlite3
from typing import Dict, Optional
from ..models.user_account import SyntheticCryptoAccount


class AccountStorage:
    def __init__(self, db_path='crypto_accounts.db'):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Создает таблицу для хранения аккаунтов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crypto_accounts (
                user_id TEXT PRIMARY KEY,
                account_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def save_account(self, account: SyntheticCryptoAccount):
        """Сохраняет аккаунт в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        account_data = {
            'account_id': account.account_id,
            'fiat_balance': account.fiat_balance,
            'crypto_balances': {
                crypto: {
                    'units': balance.units,
                    'avg_purchase_price': balance.avg_purchase_price,
                    'current_value': balance.current_value
                }
                for crypto, balance in account.crypto_balances.items()
            },
            'total_crypto_value': account.total_crypto_value,
            'last_updated': account.last_updated.isoformat()
        }

        cursor.execute('''
            INSERT OR REPLACE INTO crypto_accounts 
            (user_id, account_data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (account.user_id, json.dumps(account_data)))

        conn.commit()
        conn.close()

    def load_account(self, user_id: str) -> Optional[SyntheticCryptoAccount]:
        """Загружает аккаунт из БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT account_data FROM crypto_accounts WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            data = json.loads(result[0])
            return self._deserialize_account(user_id, data)
        return None

    def _deserialize_account(self, user_id: str, data: dict) -> SyntheticCryptoAccount:
        """Восстанавливает объект аккаунта из JSON"""
        account = SyntheticCryptoAccount(
            user_id=user_id,
            account_id=data['account_id'],
            fiat_balance=data['fiat_balance']
        )

        for crypto, balance_data in data['crypto_balances'].items():
            account.crypto_balances[crypto] = CryptoSyntheticBalance(
                currency=crypto,
                units=balance_data['units'],
                avg_purchase_price=balance_data['avg_purchase_price'],
                current_value=balance_data['current_value']
            )

        account.total_crypto_value = data['total_crypto_value']
        return account