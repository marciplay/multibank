from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Transaction(BaseModel):
    id: str
    account_id: str
    amount: float
    currency: str = "RUB"
    description: str
    date: datetime
    type: str