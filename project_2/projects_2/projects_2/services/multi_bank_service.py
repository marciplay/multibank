import asyncio
from typing import Dict, List, Any, Optional, Union
from services.bank_service import BankService
from config import settings
import logging

logger = logging.getLogger(__name__)


from models.payment_consent import (
    SingleUseConsentWithCreditorRequest,
    SingleUseConsentWithoutCreditorRequest,
    MultiUseConsentRequest,
    VRPConsentRequest,
    PaymentConsentResponse,
    PaymentConsentRequest
)

class MultiBankService:
    def __init__(self):
        self.bank_services: Dict[str, BankService] = {}
        self.active_connections: Dict[str, Dict[str, str]] = {}

    def add_bank_connection(self, bank_config: Dict[str, str]):
        """
        Добавляет новое подключение к банку.
        bank_config: {"name": "...", "api_base_url": "...", "client_id": "...", ...}
        """
        bank_name = bank_config['name']
        if bank_name in self.active_connections:
            logger.warning(f"Подключение к банку {bank_name} уже существует. Перезаписываю.")


        service = BankService(bank_config)
        self.bank_services[bank_name] = service
        self.active_connections[bank_name] = bank_config
        logger.info(f"Добавлено подключение к банку: {bank_name}")

    def remove_bank_connection(self, bank_name: str):
        """
        Удаляет подключение к банку.
        """
        if bank_name in self.bank_services:
            del self.bank_services[bank_name]
            del self.active_connections[bank_name]
            logger.info(f"Удалено подключение к банку: {bank_name}")
        else:
            logger.warning(f"Подключение к банку {bank_name} не найдено для удаления.")

    def list_connected_banks(self) -> List[str]:
        """
        Возвращает список имён подключенных банков.
        """
        return list(self.active_connections.keys())


    async def request_payment_consent_for_specific_bank(self, bank_name: str,
                                                        payment_consent_request_data: PaymentConsentRequest

    ) -> Optional[str]:
        """
        Запрашивает *новое* согласие на платёж для клиента в указанном банке.
        request_data - это объект Pydantic-модели (например, SingleUseConsentWithCreditorRequest), полученный из API.
        Возвращает X-Consent-Id или None в случае ошибки.
        """
        service = self.bank_services.get(bank_name)
        if not service:
            logger.error(f"Сервис для банка {bank_name} не найден.")
            return None


        client_id = payment_consent_request_data.client_id

        try:
            logger.info(f"Запрашиваем новое платёжное согласие для {client_id} в банке {bank_name}")
            consent_response = await service.request_payment_consent(
                payment_consent_request_data)
            consent_id = consent_response.consent_id
            logger.info(f"Платёжное согласие для {client_id} в банке {bank_name} запрошено: {consent_id}")
            return consent_id
        except Exception as e:
            logger.error(f"Ошибка при запросе платёжного согласия для {client_id} в банке {bank_name}: {e}")
            return None

    async def request_consent_for_bank(self, bank_name: str, client_id: str) -> Optional[str]:
        """
        Запрашивает *новое* согласие на доступ к данным клиента в указанном банке.
        Возвращает X-Consent-Id или None в случае ошибки.
        """
        service = self.bank_services.get(bank_name)
        if not service:
            logger.error(f"Сервис для банка {bank_name} не найден.")
            return None

        try:
            logger.info(f"Запрашиваем новое согласие для {client_id} в банке {bank_name}")
            consent_id = await service.request_consent(client_id)
            logger.info(f"Согласие для {client_id} в банке {bank_name} запрошено: {consent_id}")
            return consent_id
        except Exception as e:
            logger.error(f"Ошибка при запросе согласия для {client_id} в банке {bank_name}: {e}")
            return None

    async def get_accounts_for_single_bank(self, bank_name: str, specific_client_ids: List[str]) -> Optional[Dict[str,
    List[Dict[str, Any]]]]:
        """
        Получает все счета для указанных клиентов указанного банка.
        """
        service = self.bank_services.get(bank_name)
        if not service:
            logger.error(f"Сервис для банка {bank_name} не найден.")
            return None

        try:
            logger.info(f"Начинаем сбор данных для банка {bank_name}, клиенты: {specific_client_ids}")
            accounts = await service.get_all_accounts_for_client_list(specific_client_ids)
            logger.info(f"Завершён сбор данных для банка {bank_name}, получено клиентов: {len(accounts)}")
            return accounts
        except Exception as e:
            logger.error(f"Ошибка при сборе данных для банка {bank_name}: {e}")
            return None

    async def execute_payment_for_specific_bank(self, bank_name: str, client_id: str, consent_id: str, payment_data: dict

    ) -> Optional[Dict[str, Any]]:
        """
        Выполняет платёж в указанном банке на основе предоставленного consent_id.
        payment_data - это словарь (dict), полученный из model_dump() Pydantic-модели из API.
        Возвращает ответ от API банка или None в случае ошибки.
        """
        service = self.bank_services.get(bank_name)
        if not service:
            logger.error(f"Сервис для банка {bank_name} не найден.")
            return None

        try:
            logger.info(f"Выполняем платёж для {client_id} с consent_id {consent_id} в банке {bank_name}")

            payment_response = await service.execute_payment(client_id, consent_id,
                                                             payment_data)
            logger.info(
                f"Платёж для {client_id} в банке {bank_name} выполнен: {payment_response.data.get('paymentId')}, статус: {payment_response.data.get('status')}")
            return payment_response.model_dump()
        except Exception as e:
            logger.error(f"Ошибка при выполнении платежа для {client_id} в банке {bank_name}: {e}")
            return None
    async def get_accounts_for_multiple_banks(self, bank_requests: List[Dict[str, List[str]]]) -> Dict[str, Optional[Dict[str, List[Dict[str, Any]]]]]: # <-- Изменён формат аргумента
        """
        Получает данные для списка банков и их клиентов параллельно.
        bank_requests: [{"bank_name": "vbank", "client_ids": ["team020-1"]}, ...]
        """

        connected_banks = self.list_connected_banks()
        requested_banks = [req["bank_name"] for req in bank_requests]
        missing_banks = set(requested_banks) - set(connected_banks)
        if missing_banks:
            logger.error(f"Банки не найдены: {list(missing_banks)}")

            results = {}
            for req in bank_requests:
                bank_name = req["bank_name"]
                if bank_name in missing_banks:
                    results[bank_name] = None
                else:
                    client_ids = req["client_ids"]
                    task_result = await self.get_accounts_for_single_bank(bank_name, client_ids)
                    results[bank_name] = task_result
            return results


        tasks = []
        for req in bank_requests:
            bank_name = req["bank_name"]
            client_ids = req["client_ids"]
            task = self.get_accounts_for_single_bank(bank_name, client_ids)
            tasks.append(task)


        results = await asyncio.gather(*tasks, return_exceptions=True)


        combined_results = {}
        for i, req in enumerate(bank_requests):
            bank_name = req["bank_name"]
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"Ошибка при сборе данных для банка {bank_name}: {result}")
                combined_results[bank_name] = None
            else:
                combined_results[bank_name] = result

        return combined_results


multi_bank_service = MultiBankService()


async def initialize_connections():
    """
    Инициализирует подключения к банкам из конфига.
    """
    for bank_conf in settings.bank_configs:
        multi_bank_service.add_bank_connection(bank_conf)
