from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional, Union
from services.multi_bank_service import multi_bank_service
from models.account import Account
from models.consent import ConsentRequest, ConsentResponse
from models.payment_consent import PaymentConsentRequest, PaymentConsentResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/banks", tags=["banks"])



@router.post("/{bank_name}/request-payment-consent", response_model=PaymentConsentResponse)
async def request_payment_consent_for_bank(
        bank_name: str,
        request_data: PaymentConsentRequest
):
    """
    Запрашивает *новое* согласие на платёж для клиента в указанном банке.
    Тип согласия определяется по полю 'consent_type' в теле запроса.
    Возвращает X-Consent-Id. Пользователь должен подтвердить это согласие (если требуется).
    """
    connected_banks = multi_bank_service.list_connected_banks()
    if bank_name not in connected_banks:
        raise HTTPException(status_code=404, detail=f"Банк '{bank_name}' не подключен.")

    client_id = request_data.client_id

    consent_id = await multi_bank_service.request_payment_consent_for_specific_bank(bank_name, request_data)
    if consent_id is None:
        raise HTTPException(status_code=500,
                            detail=f"Ошибка при запросе платёжного согласия для {client_id} в банке {bank_name}.")



    return PaymentConsentResponse(
        request_id="temp_req_id",
        consent_id=consent_id,
        status="pending",
        consent_type=request_data.consent_type,
        auto_approved=False,
        message="Согласие запрошено, ожидается подтверждение"
    )



@router.post("/request-account-consent", response_model=ConsentResponse)
async def request_account_consent_for_client(request: ConsentRequest):
    """
    Запрашивает *новое* согласие на доступ к данным клиента в указанном банке.
    Возвращает X-Consent-Id. Пользователь должен подтвердить это согласие (если требуется).
    """
    consent_id = await multi_bank_service.request_consent_for_bank(request.bank_name, request.client_id)
    if consent_id is None:
        raise HTTPException(status_code=404,
                            detail=f"Банк '{request.bank_name}' не найден или ошибка при запросе согласия.")



    return ConsentResponse(consent_id=consent_id, bank_name=request.bank_name, client_id=request.client_id,
                           status="pending")



@router.get("/{bank_name}/accounts", response_model=Dict[str, List[Account]])
async def get_accounts_for_bank(
        bank_name: str,
        client_ids: List[str] = Query(..., alias="client_id")
):
    """
    Получает все счета, детали, балансы и транзакции для указанных клиентов в конкретном банке.
    ИСПОЛЬЗУЕТ СУЩЕСТВУЮЩЕЕ consent_id из файла для каждого клиента.
    """

    accounts_data = await multi_bank_service.get_accounts_for_single_bank(bank_name, client_ids)
    if accounts_data is None:
        raise HTTPException(status_code=404, detail=f"Банк '{bank_name}' не найден или ошибка при сборе данных.")


    transformed_accounts = {}
    for client_id, raw_details_list in accounts_data.items():
        account_objects = []
        for raw_detail in raw_details_list:
            logger.info(f"Обрабатываем raw_detail: {raw_detail}")
            try:
                account_obj = Account(
                    id=raw_detail.get("id", raw_detail.get("accountId", "unknown_id")),
                    identification=raw_detail.get("identification"),
                    balance=raw_detail.get("balance"),
                    currency=raw_detail.get("currency", "RUB"),
                    client_id=client_id,
                    bank_name=bank_name,
                    status=raw_detail.get("status"),
                    account_type=raw_detail.get("accountType"),
                    account_sub_type=raw_detail.get("accountSubType"),
                    description=raw_detail.get("description"),
                    nickname=raw_detail.get("nickname"),
                    opening_date=raw_detail.get("openingDate"),
                    balances=raw_detail.get("balances"),
                    transactions=raw_detail.get("transactions")
                )
                logger.info(f"Создан объект Account: {account_obj}")
                account_objects.append(account_obj)
            except Exception as e:
                logger.error(f"Ошибка при создании объекта Account из {raw_detail}: {e}")
                continue
        transformed_accounts[client_id] = account_objects

    logger.info(f"Преобразованные данные для банка {bank_name} перед сериализацией: {transformed_accounts}")
    return transformed_accounts


@router.post("/accounts_bulk", response_model=Dict[str, Optional[Dict[str, List[Account]]]])
async def get_accounts_for_banks(bank_requests: List[Dict[str, List[str]]]):
    """
    Получает данные для списка банков и их клиентов параллельно.
    Тело запроса: [{"bank_name": "vbank", "client_ids": ["team020-1"]}, ...]
    """

    connected_banks = multi_bank_service.list_connected_banks()
    requested_banks = [req["bank_name"] for req in bank_requests]
    missing_banks = set(requested_banks) - set(connected_banks)
    if missing_banks:
        raise HTTPException(status_code=404, detail=f"Банки не найдены: {list(missing_banks)}")

    prepared_requests = [{"bank_name": req["bank_name"], "client_ids": req["client_ids"]} for req in bank_requests]

    logger.info(f"Подготовленные запросы для сервиса: {prepared_requests}")
    results = await multi_bank_service.get_accounts_for_multiple_banks(prepared_requests)
    logger.info(f"Получены результаты из сервиса: {results}")

    transformed_results = {}
    for bank_name, clients_data in results.items():
        if clients_data is None:
            transformed_results[bank_name] = None
            continue

        transformed_clients = {}
        for client_id, raw_details_list in clients_data.items():
            account_objects = []
            for raw_detail in raw_details_list:
                try:
                    account_obj = Account(
                        id=raw_detail.get("id", raw_detail.get("accountId", "unknown_id")),
                        identification=raw_detail.get("identification"),
                        balance=raw_detail.get("balance"),
                        currency=raw_detail.get("currency", "RUB"),
                        client_id=client_id,
                        bank_name=bank_name,
                        status=raw_detail.get("status"),
                        account_type=raw_detail.get("accountType"),
                        account_sub_type=raw_detail.get("accountSubType"),
                        description=raw_detail.get("description"),
                        nickname=raw_detail.get("nickname"),
                        opening_date=raw_detail.get("openingDate"),
                        balances=raw_detail.get("balances"),
                        transactions=raw_detail.get("transactions")
                    )
                    account_objects.append(account_obj)
                except Exception as e:
                    logger.error(
                        f"[{bank_name}] Ошибка при создании объекта Account из {raw_detail} для клиента {client_id}: {e}")
                    continue
            transformed_clients[client_id] = account_objects
        transformed_results[bank_name] = transformed_clients


    logger.info(f"Преобразованные данные для bulk перед сериализацией: {transformed_results}")
    return transformed_results


@router.post("/connect")
async def connect_bank(bank_config: Dict[str, str]):
    """
    Добавляет новое подключение к банку.
    """
    required_keys = {"name", "api_base_url", "client_id", "client_secret"}
    if not all(key in bank_config for key in required_keys):
        raise HTTPException(status_code=400,
                            detail=f"Отсутствуют обязательные поля в конфигурации банка. Требуется: {required_keys}")

    multi_bank_service.add_bank_connection(bank_config)
    return {"message": f"Подключение к банку {bank_config['name']} добавлено."}


@router.delete("/disconnect/{bank_name}")
async def disconnect_bank(bank_name: str):
    """
    Удаляет подключение к банку.
    """
    multi_bank_service.remove_bank_connection(bank_name)
    return {"message": f"Подключение к банку {bank_name} удалено."}



@router.get("/connections")
async def list_connections():
    """
    Возвращает список подключенных банков.
    """
    connected_banks = multi_bank_service.list_connected_banks()
    return {"connected_banks": connected_banks}
