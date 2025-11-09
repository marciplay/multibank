from pydantic import BaseModel
from typing import Optional

class ConsentRequest(BaseModel):
    bank_name: str
    client_id: str

class ConsentResponse(BaseModel):
    consent_id: str
    bank_name: str
    client_id: str
    status: str
    message: Optional[str] = None