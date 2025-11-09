from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BalanceAmount(BaseModel):
    amount: str
    currency: str

class BalanceItem(BaseModel):
    accountId: str
    type: str
    dateTime: str
    amount: BalanceAmount
    creditDebitIndicator: str

class TransactionAmount(BaseModel):
    amount: str
    currency: str

class TransactionItem(BaseModel):
    transactionId: str
    accountId: str
    amount: TransactionAmount
    creditDebitIndicator: str
    status: str
    bookingDateTime: str
    valueDateTime: str
    transactionInformation: str



class Account(BaseModel):
    id: str
    identification: Optional[str] = None
    balance: Optional[float] = None
    currency: str = "RUB"
    client_id: str
    bank_name: str
    status: Optional[str] = None
    account_type: Optional[str] = None
    account_sub_type: Optional[str] = None
    description: Optional[str] = None
    nickname: Optional[str] = None
    opening_date: Optional[str] = None
    balances: Optional[List[BalanceItem]] = None
    transactions: Optional[List[TransactionItem]] = None