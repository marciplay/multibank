from fastapi import APIRouter, Depends, HTTPException
from typing import Union # <-- Добавлено
from services.bank_service import BankService
from services.multi_bank_service import multi_bank_service
from models.consent import ConsentRequest, ConsentResponse
from models.payment_consent import (
    SingleUseConsentWithCreditorRequest,
    SingleUseConsentWithoutCreditorRequest,
    MultiUseConsentRequest,
    VRPConsentRequest,
    PaymentConsentResponse,
    PaymentRequestData,
    PaymentStatusResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/request-consent", response_model=PaymentConsentResponse)
async def request_payment_consent_endpoint(
    request_data: Union[SingleUseConsentWithCreditorRequest, SingleUseConsentWithoutCreditorRequest, MultiUseConsentRequest,
    VRPConsentRequest], bank_service: BankService = Depends()
):
    """
    Запрашивает согласие на выполнение платежа (Single Use, Multi Use, VRP).
    Тип согласия определяется по полю 'consent_type' в теле запроса.
    """
    try:
        logger.info(f"Получен запрос на согласие на платёж: {request_data.model_dump()}")
        consent_response = await bank_service.request_payment_consent(request_data)
        return consent_response
    except Exception as e:
        logger.error(f"Ошибка при запросе согласия на платёж: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе согласия на платёж: {str(e)}")


@router.post("/execute", response_model=PaymentStatusResponse)
async def execute_payment_endpoint(
    client_id: str,
    consent_id: str,
    bank_name: str,
    payment_data: dict,
):
    """
    Выполняет платёж на основе предоставленного consent_id в указанном банке.
    """
    try:
        logger.info(f"Получен запрос на выполнение платежа для клиента {client_id} с consent_id {consent_id} в банке {bank_name}")
        logger.info(f"Тело запроса на выполнение платежа: {payment_data}")


        service = multi_bank_service.bank_services.get(bank_name)
        if not service:
            raise HTTPException(status_code=404, detail=f"Банк '{bank_name}' не найден или не подключен.")

        payment_response = await service.execute_payment(client_id, consent_id, payment_data)
        return payment_response

    except Exception as e:
        logger.error(f"Ошибка при выполнении платежа: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при выполнении платежа: {str(e)}")


@router.get("/status/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: str,
    client_id: str,
    bank_service: BankService = Depends()
):
    """
    Получает статус выполненного платежа.
    """
    try:
        raise HTTPException(status_code=501, detail="Получение статуса платежа пока не реализовано.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статуса платежа: {str(e)}")
