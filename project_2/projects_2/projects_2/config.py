from pydantic_settings import BaseSettings
from typing import List, Dict

class Settings(BaseSettings):
    app_name: str = "MultiBank Aggregator"
    debug: bool = True

    bank_configs: List[Dict[str, str]] = [
        {
            "name": "vbank",
            "api_base_url": "https://vbank.open.bankingapi.ru",
            "client_id": "team020",
            "client_secret": "PfA7bDk1k14ppzJO9j7ZCTyNEIgOlF45",
        },
        {
            "name": "abank",
            "api_base_url": "https://abank.open.bankingapi.ru",
            "client_id": "team020",
            "client_secret": "PfA7bDk1k14ppzJO9j7ZCTyNEIgOlF45",
        },
        {
            "name": "sbank",
            "api_base_url": "https://sbank.open.bankingapi.ru",
            "client_id": "team020",
            "client_secret": "PfA7bDk1k14ppzJO9j7ZCTyNEIgOlF45",
        }
    ]

    class Config:
        env_file = ".env"

settings = Settings()