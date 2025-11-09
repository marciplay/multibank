import httpx
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union
from auth.bank_auth import BankAuthClient
from config import settings
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)


from typing import Union


from models.payment_consent import (
    SingleUseConsentWithCreditorRequest,
    SingleUseConsentWithoutCreditorRequest,
    MultiUseConsentRequest,
    VRPConsentRequest,
    PaymentConsentResponse,
    PaymentRequestData,
    PaymentStatusResponse
)

class BankAPIError(Exception):
    pass


class BankService:
    def __init__(self, bank_config: Dict[str, str]):
        self.auth_client = BankAuthClient(
            base_url=bank_config['api_base_url'],
            client_id=bank_config['client_id'],
            client_secret=bank_config['client_secret']
        )
        self.token: Optional[str] = None
        self.bank_name = bank_config['name']
        self.consent_ids: Dict[str, str] = self._load_consents()
        self.payment_consent_ids: Dict[str, str] = self._load_payment_consents()

    def _get_consent_filename(self):
        """Возвращает имя файла для consent_ids, уникальное для банка."""
        return f"consents_{self.bank_name}.json"

    def _get_payment_consent_filename(self):
        """Возвращает имя файла для payment_consent_ids, уникальное для банка."""
        return f"payment_consents_{self.bank_name}.json"

    def _load_consents(self) -> Dict[str, str]:
        """Загружает сохранённые consent_id из файла."""
        filename = self._get_consent_filename()
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info(f"Файл {filename} не найден, создаём пустой словарь.")
            return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки {filename}: {e}")
            return {}

    def _save_consents(self):
        """Сохраняет текущие consent_id в файл."""
        filename = self._get_consent_filename()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.consent_ids, f, ensure_ascii=False, indent=2)
        logger.info(f"Consents сохранены в {filename}")

    def _remove_consent(self, client_id: str):
        """Удаляет consent_id для клиента из кэша и файла."""
        if client_id in self.consent_ids:
            consent_id = self.consent_ids.pop(client_id)
            self._save_consents()
            logger.info(f"Consent ID {consent_id} для {client_id} удалён из кэша и файла.")

    def _load_payment_consents(self) -> Dict[str, str]:
        """Загружает сохранённые payment consent_id из файла."""
        filename = self._get_payment_consent_filename()
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info(f"Файл {filename} не найден, создаём пустой словарь.")
            return {}
        except Exception as e:
            logger.error(f"Ошибка загрузки {filename}: {e}")
            return {}

    def _save_payment_consents(self):
        """Сохраняет текущие payment consent_id в файл."""
        filename = self._get_payment_consent_filename()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.payment_consent_ids, f, ensure_ascii=False, indent=2)
        logger.info(f"Payment consents сохранены в {filename}")

    def _remove_payment_consent(self, consent_id: str):
        """Удаляет payment consent_id из кэша и файла."""
        if consent_id in self.payment_consent_ids:
            removed_id = self.payment_consent_ids.pop(consent_id)
            self._save_payment_consents()
            logger.info(f"Payment Consent ID {removed_id} удалён из кэша и файла.")

    async def authenticate(self):
        """Аутентифицируется и получает токен"""
        if not self.token:
            self.token = await self.auth_client.get_token()
            logger.info("Токен получен")

    async def request_consent_if_needed(self, client_id: str, max_retries: int = 5) -> str:
        """
        Запрашивает согласие, только если его нет в self.consent_ids.
        В случае ошибки, повторяет до max_retries раз.
        Возвращает X-Consent-Id.
        """
        consent_id = self.consent_ids.get(client_id)
        if consent_id:
            logger.info(f"[{self.bank_name}] Consent ID для {client_id} уже существует: {consent_id}")
            return consent_id

        logger.info(f"[{self.bank_name}] Consent ID для {client_id} не найден, запрашиваем новый...")
        if not self.token:
            await self.authenticate()

        url = f"{self.auth_client.base_url}/account-consents/request"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Requesting-Bank": self.auth_client.client_id,
            "Content-Type": "application/json"
        }

        body = {
            "client_id": client_id,
            "permissions": ["ReadAccountsDetail", "ReadBalances", "ReadTransactionsDetail"],
            "reason": "Агрегация счетов для HackAPI",
            "requesting_bank": self.auth_client.client_id,
            "requesting_bank_name": "Team 020 App"
        }


        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=body)
                    response.raise_for_status()

                    logger.info(
                        f"[{self.bank_name}] Заголовки ответа от /account-consents/request для {client_id}: {dict(response.headers)}")
                    response_body = response.json()
                    logger.info(f"[{self.bank_name}] Тело ответа от /account-consents/request для {client_id}: {response_body}")


                    consent_id = response.headers.get("X-Consent-Id")
                    logger.info(f"[{self.bank_name}] X-Consent-Id из заголовков: {consent_id}")
                    if not consent_id:
                        consent_id = response_body.get("consent_id") or response_body.get("id")
                        logger.info(f"[{self.bank_name}] X-Consent-Id из тела: {consent_id}")

                    if not consent_id:
                        raise BankAPIError("Не удалось получить X-Consent-Id из ответа")

                    self.consent_ids[client_id] = consent_id
                    self._save_consents()
                    logger.info(f"[{self.bank_name}] Согласие получено и сохранено для {client_id}: {consent_id}")
                    return consent_id
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                logger.error(
                    f"[{self.bank_name}] HTTP ошибка при запросе согласия для {client_id} (попытка {attempt + 1}/{max_retries}): {status_code} - {response_text}")
                if status_code == 429 or 500 <= status_code < 600:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue
                if status_code in [400, 401, 403] and (
                        "consent" in response_text.lower() or "invalid" in response_text.lower() or "revoked" in response_text.lower()):
                    self._remove_consent(client_id)
                    raise
                raise
            except Exception as e:
                logger.error(f"[{self.bank_name}] Ошибка при запросе согласия для {client_id} (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    continue
                raise


    async def request_consent(self, client_id: str, max_retries: int = 5) -> Optional[str]:
        """
        Запрашивает *новое* согласие для клиента в этом банке.
        Возвращает X-Consent-Id, если согласие выдано автоматически (auto_approved == True).
        Возвращает None, если согласие требует ручного подтверждения (auto_approved == False).
        """
        if not self.token:
            await self.authenticate()

        url = f"{self.auth_client.base_url}/account-consents/request"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Requesting-Bank": self.auth_client.client_id,
            "Content-Type": "application/json"
        }

        body = {
            "client_id": client_id,
            "permissions": ["ReadAccountsDetail", "ReadBalances", "ReadTransactionsDetail"],
            "reason": "Агрегация счетов для HackAPI",
            "requesting_bank": self.auth_client.client_id,
            "requesting_bank_name": "Team 020 App"
        }

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=body)
                    response.raise_for_status()


                    logger.info(
                        f"[{self.bank_name}] Заголовки ответа от /account-consents/request для {client_id}: {dict(response.headers)}")
                    response_body = response.json()
                    logger.info(f"[{self.bank_name}] Тело ответа от /account-consents/request для {client_id}: {response_body}")

                    auto_approved = response_body.get("auto_approved", False)
                    logger.info(f"[{self.bank_name}] auto_approved для {client_id}: {auto_approved}")

                    if not auto_approved:
                        logger.info(f"[{self.bank_name}] Согласие для {client_id} требует ручного подтверждения. Завершаем запрос.")
                        return None
                    else:
                        logger.info(f"[{self.bank_name}] Согласие для {client_id} выдано автоматически. Ищем consent_id...")

                        consent_id = response.headers.get("X-Consent-Id")
                        logger.info(f"[{self.bank_name}] X-Consent-Id из заголовков: {consent_id}")
                        if not consent_id:
                            consent_id = response_body.get("consent_id") or response_body.get("id")
                            logger.info(f"[{self.bank_name}] X-Consent-Id из тела: {consent_id}")

                        if not consent_id:
                            raise BankAPIError("Не удалось получить X-Consent-Id из ответа, несмотря на auto_approved=True")


                        logger.info(f"[{self.bank_name}] Запрошено новое согласие для {client_id}, consent_id: {consent_id}")
                        return consent_id
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                logger.error(
                    f"[{self.bank_name}] HTTP ошибка при запросе согласия для {client_id} (попытка {attempt + 1}/{max_retries}): {status_code} - {response_text}")
                if status_code == 429 or 500 <= status_code < 600:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                logger.error(f"[{self.bank_name}] Ошибка при запросе согласия для {client_id} (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    continue
                raise

    async def get_account_list(self, client_id: str, consent_id: str, max_retries: int = 5) -> List[Dict[str, Any]]:
        """
        Получает список счетов (только ID и основная информация) для клиента.
        """
        if not self.token:
            await self.authenticate()

        url = f"{self.auth_client.base_url}/accounts?client_id={client_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Requesting-Bank": self.auth_client.client_id,
            "X-Consent-Id": consent_id
        }

        logger.info(f"[{self.bank_name}] Запрашиваем список счетов для {client_id} с consent_id: {consent_id}")
        logger.info(f"[{self.bank_name}] Ждём 10 секунд перед запросом списка счетов...")
        await asyncio.sleep(10)
        logger.info(f"[{self.bank_name}] Отправляем запрос на /accounts для {client_id} после задержки.")

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    logger.info(f"[{self.bank_name}] Ответ от /accounts для {client_id}: {data}")


                    accounts = data.get("data", {}).get("account", [])
                    logger.info(f"[{self.bank_name}] Извлечённые счета из /accounts для {client_id}: {accounts}")


                    logger.info(f"[{self.bank_name}] Получено {len(accounts)} счетов в списке для {client_id}")
                    return accounts
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                logger.error(
                    f"[{self.bank_name}] HTTP ошибка при запросе списка счетов для {client_id} (попытка {attempt + 1}/{max_retries}): {status_code} - {response_text}")

                if status_code in [400, 401, 403] and (
                        "consent" in response_text.lower() or "invalid" in response_text.lower() or "revoked" in response_text.lower()):
                    logger.warning(f"[{self.bank_name}] Согласие для {client_id} ({consent_id}) возможно отозвано или недействительно.")
                    self._remove_consent(client_id)
                    logger.info(f"[{self.bank_name}] Повторно запрашиваем согласие для {client_id}...")
                    new_consent_id = await self.request_consent_if_needed(client_id)
                    logger.info(
                        f"[{self.bank_name}] Повторно запрашиваем список счетов для {client_id} с новым consent_id: {new_consent_id}")
                    return await self._fetch_account_list_with_consent(client_id, new_consent_id, retry_count=0)
                elif status_code == 429 or 500 <= status_code < 600:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                logger.error(
                    f"[{self.bank_name}] Ошибка при запросе списка счетов для {client_id} (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    continue
                raise

    async def _fetch_account_list_with_consent(self, client_id: str, consent_id: str, retry_count: int = 0,
                                               max_retries: int = 1) -> List[Dict[str, Any]]:
        """
        Внутренний метод для запроса списка счетов с обработкой ошибок и повторных попыток.
        """
        if retry_count > max_retries:
            raise BankAPIError(f"[{self.bank_name}] Превышено количество попыток запроса списка счетов для {client_id}")

        if not self.token:
            await self.authenticate()

        url = f"{self.auth_client.base_url}/accounts?client_id={client_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Requesting-Bank": self.auth_client.client_id,
            "X-Consent-Id": consent_id
        }

        logger.info(f"[{self.bank_name}] Запрашиваем список счетов для {client_id} с consent_id: {consent_id} (попытка {retry_count + 1})")

        logger.info(f"[{self.bank_name}] Ждём 10 секунд перед запросом списка счетов...")
        await asyncio.sleep(10)
        logger.info(f"[{self.bank_name}] Отправляем запрос на /accounts для {client_id} после задержки.")


        for attempt in range(5):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    logger.info(f"[{self.bank_name}] Ответ от /accounts для {client_id}: {data}")


                    accounts = data.get("data", {}).get("account", [])


                    logger.info(f"[{self.bank_name}] Получено {len(accounts)} счетов в списке для {client_id}")
                    return accounts
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                logger.error(
                    f"[{self.bank_name}] HTTP ошибка при запросе списка счетов для {client_id} (попытка {attempt + 1}/5): {status_code} - {response_text}")

                if status_code in [400, 401, 403] and (
                        "consent" in response_text.lower() or "invalid" in response_text.lower() or "revoked" in response_text.lower()):
                    if retry_count < max_retries:
                        logger.warning(
                            f"[{self.bank_name}] Согласие для {client_id} ({consent_id}) возможно отозвано. Удаляем и запрашиваем новое.")
                        self._remove_consent(client_id)
                        new_consent_id = await self.request_consent_if_needed(client_id)
                        return await self._fetch_account_list_with_consent(client_id, new_consent_id, retry_count + 1)
                    else:
                        logger.error(f"[{self.bank_name}] Не удалось получить список счетов для {client_id} после повторных попыток.")
                        raise BankAPIError(
                            f"[{self.bank_name}] Согласие для {client_id} недействительно и не удалось получить новое: {response_text}")
                elif status_code == 429 or 500 <= status_code < 600:
                    if attempt < 4:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                logger.error(f"[{self.bank_name}] Ошибка при запросе списка счетов для {client_id} (попытка {attempt + 1}/5): {e}")
                if attempt < 4:
                    wait_time = 2 ** attempt
                    logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    continue
                raise

    async def get_account_detail(self, client_id: str, consent_id: str, account_id: str, max_retries: int = 5) -> \
    Optional[Dict[str, Any]]:
        """
        Получает детальную информацию о конкретном счёте.
        """
        if not self.token:
            await self.authenticate()

        url = f"{self.auth_client.base_url}/accounts/{account_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Requesting-Bank": self.auth_client.client_id,
            "X-Consent-Id": consent_id,
            "Accept": "application/json"
        }

        logger.info(f"[{self.bank_name}] Запрашиваем детали счёта {account_id} для {client_id}")
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    logger.info(f"[{self.bank_name}] Детали счёта {account_id}: {data}")
                    account_details = data.get("data", {}).get("account", [])
                    if account_details:
                        return account_details[0]
                    else:
                        logger.warning(f"[{self.bank_name}] Детали счёта {account_id} пусты.")
                        return None
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                logger.error(
                    f"[{self.bank_name}] HTTP ошибка при запросе деталей счёта {account_id} (попытка {attempt + 1}/{max_retries}): {status_code} - {response_text}")
                if status_code in [400, 401, 403]:
                    if "consent" in response_text.lower() or "invalid" in response_text.lower() or "revoked" in response_text.lower():
                        logger.warning(
                            f"[{self.bank_name}] Согласие для {client_id} ({consent_id}) возможно отозвано при запросе деталей счёта {account_id}.")
                        self._remove_consent(client_id)

                        return None
                elif status_code == 429 or 500 <= status_code < 600:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue

                logger.error(f"[{self.bank_name}] Не удалось получить детали для счёта {account_id}: {e}. Пропускаем.")
                return None
            except Exception as e:
                logger.error(
                    f"[{self.bank_name}] Ошибка при запросе деталей счёта {account_id} (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    continue

                logger.error(f"[{self.bank_name}] Не удалось получить детали для счёта {account_id}: {e}. Пропускаем.")
                return None

    async def get_balance_for_account(self, client_id: str, consent_id: str, account_id: str, max_retries: int = 5) -> \
    Optional[List[Dict[str, Any]]]:
        """
        Получает балансы для конкретного счёта.
        """
        if not self.token:
            await self.authenticate()

        url = f"{self.auth_client.base_url}/accounts/{account_id}/balances"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Requesting-Bank": self.auth_client.client_id,
            "X-Consent-Id": consent_id,
            "Accept": "application/json"
        }

        logger.info(f"[{self.bank_name}] Запрашиваем балансы для счёта {account_id} для {client_id}")
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    logger.info(f"[{self.bank_name}] Балансы для счёта {account_id}: {data}")
                    balances = data.get("data", {}).get("balance", [])
                    return balances
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                logger.error(
                    f"[{self.bank_name}] HTTP ошибка при запросе баланса для счёта {account_id} (попытка {attempt + 1}/{max_retries}): {status_code} - {response_text}")
                if status_code in [400, 401, 403]:
                    if "consent" in response_text.lower() or "invalid" in response_text.lower() or "revoked" in response_text.lower():
                        logger.warning(
                            f"[{self.bank_name}] Согласие для {client_id} ({consent_id}) возможно отозвано при запросе баланса счёта {account_id}.")
                        self._remove_consent(client_id)
                        return None
                elif status_code == 429 or 500 <= status_code < 600:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue
                logger.error(f"[{self.bank_name}] Не удалось получить баланс для счёта {account_id}: {e}. Пропускаем.")
                return None
            except Exception as e:
                logger.error(
                    f"[{self.bank_name}] Ошибка при запросе баланса для счёта {account_id} (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"[{self.bank_name}] Не удалось получить баланс для счёта {account_id}: {e}. Пропускаем.")
                return None

    async def get_transactions_for_account(self, client_id: str, consent_id: str, account_id: str,
                                           max_retries: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Получает ВСЕ транзакции для конкретного счёта.
        """
        if not self.token:
            await self.authenticate()

        all_transactions = []
        page = 1
        limit = 100
        while True:
            url = f"{self.auth_client.base_url}/accounts/{account_id}/transactions?page={page}&limit={limit}"
            headers = {
                "Authorization": f"Bearer {self.token}",
                "X-Requesting-Bank": self.auth_client.client_id,
                "X-Consent-Id": consent_id,
                "Accept": "application/json"
            }

            logger.info(f"[{self.bank_name}] Запрашиваем транзакции для счёта {account_id}, страница {page}...")
            page_transactions = []
            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, headers=headers)
                        response.raise_for_status()

                        data = response.json()
                        logger.info(f"[{self.bank_name}] Транзакции для счёта {account_id}, страница {page}: {data}")
                        page_transactions = data.get("data", {}).get("transaction", [])
                        break
                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    response_text = e.response.text
                    logger.error(
                        f"[{self.bank_name}] HTTP ошибка при запросе транзакций для счёта {account_id}, страница {page} (попытка {attempt + 1}/{max_retries}): {status_code} - {response_text}")
                    if status_code in [400, 401, 403]:
                        if "consent" in response_text.lower() or "invalid" in response_text.lower() or "revoked" in response_text.lower():
                            logger.warning(
                                f"[{self.bank_name}] Согласие для {client_id} ({consent_id}) возможно отозвано при запросе транзакций счёта {account_id}.")
                            self._remove_consent(client_id)
                            return None
                    elif status_code == 429 or 500 <= status_code < 600:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                            await asyncio.sleep(wait_time)
                            continue
                    logger.error(
                        f"[{self.bank_name}] Не удалось получить транзакции для счёта {account_id}, страница {page}: {e}. Пропускаем.")
                    return None
                except Exception as e:
                    logger.error(
                        f"[{self.bank_name}] Ошибка при запросе транзакций для счёта {account_id}, страница {page} (попытка {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue
                    logger.error(
                        f"[{self.bank_name}] Не удалось получить транзакции для счёта {account_id}, страница {page}: {e}. Пропускаем.")
                    return None

            if not page_transactions:
                logger.info(f"[{self.bank_name}] Нет больше транзакций для счёта {account_id} на странице {page}.")
                break

            all_transactions.extend(page_transactions)
            logger.info(
                f"[{self.bank_name}] Получено {len(page_transactions)} транзакций со страницы {page} для счёта {account_id}. Всего накоплено: {len(all_transactions)}")
            page += 1

        return all_transactions

    async def get_all_account_details(self, client_id: str, consent_id: str) -> List[Dict[str, Any]]:
        """
        Получает список всех счетов, затем для каждого запрашивает детали, балансы и транзакции.
        Добавляет 'identification' из списка в итоговую запись счёта.
        """
        logger.info(f"[{self.bank_name}] Получаем список счетов для {client_id}...")
        account_list = await self.get_account_list(client_id, consent_id)

        all_details = []
        for acc_summary in account_list:
            acc_id = acc_summary.get("accountId")
            acc_account_array = acc_summary.get("account", [])
            acc_identification = None
            if acc_account_array:
                first_account_details = acc_account_array[0]
                acc_identification = first_account_details.get("identification")


            if not acc_id:
                logger.warning(f"[{self.bank_name}] Счёт без accountId в списке: {acc_summary}")
                continue

            logger.info(f"[{self.bank_name}] Получаем детали для счёта {acc_id}...")
            try:
                detail = await self.get_account_detail(client_id, consent_id, acc_id)
                if detail:

                    detail["identification"] = acc_identification


                    balances = await self.get_balance_for_account(client_id, consent_id, acc_id)

                    detail["balances"] = balances


                    transactions = await self.get_transactions_for_account(client_id, consent_id, acc_id)

                    detail["transactions"] = transactions


                    logger.info(f"[{self.bank_name}] Детали счёта {acc_id} перед добавлением: {detail}")


                    all_details.append(detail)
            except Exception as e:
                logger.error(f"[{self.bank_name}] Не удалось получить детали для счёта {acc_id}: {e}. Пропускаем.")
                continue


        logger.info(f"[{self.bank_name}] Всё, что вернёт get_all_account_details для {client_id}: {all_details}")


        return all_details






    async def get_all_accounts_for_client_list(self, specific_client_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получает детальную информацию, балансы и транзакции о всех счетах для указанных клиентов этого банка.
        Использует сохранённое согласие, если оно есть.
        Обрабатывает клиентов параллельно.
        """
        if not self.token:
            await self.authenticate()

        target_client_ids = specific_client_ids

        logger.info(f"[{self.bank_name}] Начинаем параллельную обработку {len(target_client_ids)} клиентов.")


        tasks = []
        for client_id in target_client_ids:
            task = self._process_single_client(client_id)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)


        all_accounts = {}
        for i, client_id in enumerate(target_client_ids):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"[{self.bank_name}] Ошибка при обработке клиента {client_id}: {result}")
                all_accounts[client_id] = []
            else:
                all_accounts[client_id] = result
                logger.info(f"[{self.bank_name}] Получено {len(result)} счетов для клиента {client_id}")

        logger.info(f"[{self.bank_name}] Завершена параллельная обработка всех клиентов.")
        return all_accounts


    async def _process_single_client(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Обрабатывает одного клиента: запрашивает согласие, получает счета, детали, балансы, транзакции.
        """
        try:
            logger.info(f"[{self.bank_name}] Обработка клиента {client_id}...")
            consent_id = await self.request_consent_if_needed(client_id)
            accounts = await self.get_all_account_details(client_id, consent_id)
            logger.info(f"[{self.bank_name}] Завершена обработка клиента {client_id}, получено {len(accounts)} счетов")
            return accounts
        except Exception as e:
            logger.error(f"[{self.bank_name}] Критическая ошибка при обработке клиента {client_id}: {e}")
            return []



    async def request_payment_consent(self, request_data: Union[
        SingleUseConsentWithCreditorRequest, SingleUseConsentWithoutCreditorRequest, MultiUseConsentRequest, VRPConsentRequest],
                                      max_retries: int = 5

    ) -> PaymentConsentResponse:
        """
        Запрашивает согласие на платёж.
        request_data - это объект Pydantic-модели (например, SingleUseConsentWithCreditorRequest).
        """
        if not self.token:
            await self.authenticate()

        url = f"{self.auth_client.base_url}/payment-consents/request"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Requesting-Bank": self.auth_client.client_id,
            "Content-Type": "application/json"
        }

        body = request_data.model_dump()

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=body)
                    response.raise_for_status()

                    response_data = response.json()
                    logger.info(f"[{self.bank_name}] Ответ от /payment-consents/request: {response_data}")

                    consent_response = PaymentConsentResponse(**response_data)


                    self.payment_consent_ids[consent_response.consent_id] = request_data.client_id
                    self._save_payment_consents()

                    logger.info(
                        f"[{self.bank_name}] Согласие на платёж получено: {consent_response.consent_id} для клиента {request_data.client_id}")


                    logger.info(f"[{self.bank_name}] Ждём 10 секунд перед выполнением платежа по этому согласию...")
                    await asyncio.sleep(10)
                    logger.info(
                        f"[{self.bank_name}] Задержка завершена. Согласие {consent_response.consent_id} готово к использованию.")


                    return consent_response
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                logger.error(
                    f"[{self.bank_name}] HTTP ошибка при запросе согласия на платёж (попытка {attempt + 1}/{max_retries}): {status_code} - {response_text}")
                if status_code == 429 or 500 <= status_code < 600:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                logger.error(f"Ошибка при запросе согласия на платёж (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Ждём {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    continue
                raise


    async def execute_payment(self, client_id: str, consent_id: str, payment_data: dict, max_retries: int = 5

    ) -> PaymentStatusResponse:
        """
        Выполняет платёж на основе предоставленного consent_id.
        payment_data - это словарь (dict), полученный из model_dump() Pydantic-модели из API.
        """
        if not self.token:
            await self.authenticate()

        url = f"{self.auth_client.base_url}/payments?client_id={client_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Requesting-Bank": self.auth_client.client_id,
            "X-Payment-Consent-Id": consent_id,
            "X-FAPI-Interaction-ID": f"team020-pay-{int(time.time())}",
            "X-FAPI-Customer-IP-Address": "192.168.1.100",
            "Content-Type": "application/json"
        }


        incoming_data = payment_data.get("data", {})

        if "initiation" in incoming_data:
            vbank_request_body = payment_data
        else:
            vbank_request_body = {
                "data": {
                    "initiation": incoming_data
                }
            }

        body = vbank_request_body

        logger.info(f"[{self.bank_name}] Выполняем платёж с consent_id: {consent_id}, тело: {body}")
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=body)
                    response.raise_for_status()

                    response_data = response.json()
                    logger.info(f"[{self.bank_name}] Ответ от /payments: {response_data}")

                    payment_response = PaymentStatusResponse(**response_data)
                    logger.info(
                        f"[{self.bank_name}] Платёж выполнен: {payment_response.data.get('paymentId')}, статус: {payment_response.data.get('status')}")
                    return payment_response
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text
                logger.error(
                    f"[{self.bank_name}] HTTP ошибка при выполнении платежа (попытка {attempt + 1}/{max_retries}): {status_code} - {response_text}")
                if status_code in [400, 401, 403]:
                    if "consent" in response_text.lower() or "invalid" in response_text.lower() or "revoked" in response_text.lower():
                        logger.warning(
                            f"[{self.bank_name}] Согласие {consent_id} возможно отозвано или недействительно при выполнении платежа.")
                        self._remove_payment_consent(consent_id)
                        raise BankAPIError(
                            f"[{self.bank_name}] Согласие на платёж {consent_id} недействительно: {response_text}")
                elif status_code == 429 or 500 <= status_code < 600:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"[{self.bank_name}] Ждём {wait_time} секунд перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                        continue
                raise
            except Exception as e:
                logger.error(f"Ошибка при выполнении платежа (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Ждём {wait_time} секунд перед повторной попыткой...")
                    await asyncio.sleep(wait_time)
                    continue
                raise

    async def get_all_accounts_for_all_clients(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получает детальную информацию, балансы и транзакции о всех счетах для ВСЕХ клиентов: team020-1 .. team020-5.
        Использует сохранённое согласие, если оно есть.
        """
        if not self.token:
            await self.authenticate()

        all_accounts = {}
        for i in range(1, 6):
            client_id = f"team020-{i}"
            try:
                logger.info(f"Обработка клиента {client_id}...")
                consent_id = await self.request_consent_if_needed(client_id)
                accounts = await self.get_all_account_details(client_id, consent_id)
                all_accounts[client_id] = accounts
                logger.info(f"Получено {len(accounts)} счетов с деталями, балансами и транзакциями для {client_id}")
            except Exception as e:
                logger.error(f"Ошибка при обработке клиента {client_id}: {e}")
                all_accounts[client_id] = []

        return all_accounts