from pydantic import BaseModel
from datetime import datetime

class BankConnection(BaseModel):
    bank_name: str
    client_id: str
    connected_at: datetime
    consent_id: str
    is_active: bool = True