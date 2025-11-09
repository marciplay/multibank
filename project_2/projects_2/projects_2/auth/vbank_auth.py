import httpx
from typing import Optional
from pydantic import BaseModel
from config import settings

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int

class VBankAuthClient:
    def __init__(self):
        self.base_url = settings.bank_api_base_url
        self.client_id = settings.client_id
        self.client_secret = settings.client_secret

    async def get_token(self) -> str:
        """
        Получает токен доступа к API vBank
        """
        url = f"{self.base_url}/auth/bank-token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data["access_token"]