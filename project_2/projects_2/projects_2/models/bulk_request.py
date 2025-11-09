from pydantic import BaseModel
from typing import List

class BankAccountRequest(BaseModel):
    bank_name: str
    client_ids: List[str]