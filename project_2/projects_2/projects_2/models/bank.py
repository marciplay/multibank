from pydantic import BaseModel

class Bank(BaseModel):
    name: str
    api_base_url: str
    client_id: str