import httpx
from typing import Optional
from pydantic import BaseModel

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int

class BankAuthClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret

    async def get_token(self) -> str:
        """
        Получает токен доступа к API банка
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