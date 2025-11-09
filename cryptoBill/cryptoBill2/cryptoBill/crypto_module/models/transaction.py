from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BUY_CRYPTO = "buy_crypto"
    SELL_CRYPTO = "sell_crypto"


class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Transaction:
    transaction_id: str
    user_id: str
    type: TransactionType
    amount: float
    currency: str
    status: TransactionStatus
    created_at: datetime
    completed_at: datetime = None
    description: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def complete(self):
        self.status = TransactionStatus.COMPLETED
        self.completed_at = datetime.now()

    def fail(self, error_message: str):
        self.status = TransactionStatus.FAILED
        self.completed_at = datetime.now()
        self.metadata['error'] = error_message