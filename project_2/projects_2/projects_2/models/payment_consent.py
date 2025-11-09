from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime
from typing import Literal


class Amount(BaseModel):
    amount: str
    currency: str = "RUB"

class DebtorAccount(BaseModel):
    identification: str
    schemeName: str = "RU.CBR.PAN"

class CreditorAccountWithBankCode(BaseModel):
    identification: str
    bank_code: str
    schemeName: str = "RU.CBR.PAN"

class CreditorAccountWithoutBankCode(BaseModel):
    identification: str
    schemeName: str = "RU.CBR.PAN"

class SingleUseConsentWithCreditorRequest(BaseModel):
    requesting_bank: str
    client_id: str
    consent_type: Literal["single_use"] = "single_use"
    amount: str
    debtor_account: str
    creditor_account: str
    creditor_name: Optional[str] = None
    reference: Optional[str] = None

class SingleUseConsentWithoutCreditorRequest(BaseModel):
    requesting_bank: str
    client_id: str
    consent_type: Literal["single_use"] = "single_use"
    amount: str
    debtor_account: str
    reference: Optional[str] = None

class MultiUseConsentRequest(BaseModel):
    requesting_bank: str
    client_id: str
    consent_type: Literal["multi_use"] = "multi_use"
    debtor_account: str
    max_uses: int
    max_amount_per_payment: str
    max_total_amount: Optional[str] = None
    allowed_creditor_accounts: Optional[List[str]] = None
    valid_until: Optional[datetime] = None

class VRPConsentRequest(BaseModel):
    requesting_bank: str
    client_id: str
    consent_type: Literal["vrp"] = "vrp"
    debtor_account: str
    vrp_max_individual_amount: str
    vrp_daily_limit: str
    vrp_monthly_limit: str
    valid_until: Optional[datetime] = None

from typing import Annotated

PaymentConsentRequest = Union[
    Annotated[SingleUseConsentWithCreditorRequest, Field(discriminator="consent_type")],
    Annotated[SingleUseConsentWithoutCreditorRequest, Field(discriminator="consent_type")],
    Annotated[MultiUseConsentRequest, Field(discriminator="consent_type")],
    Annotated[VRPConsentRequest, Field(discriminator="consent_type")]
]


class PaymentConsentResponse(BaseModel):
    request_id: str
    consent_id: str
    status: str
    consent_type: str
    auto_approved: bool
    message: Optional[str] = None
    valid_until: Optional[datetime] = None


class PaymentInitiation(BaseModel):
    instructedAmount: Amount
    debtorAccount: DebtorAccount
    creditorAccount: CreditorAccountWithBankCode


class PaymentRequestData(BaseModel):
    dict


class PaymentStatusResponse(BaseModel):
    dict
    links: dict
    meta: dict
