from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, Field, field_validator

from app.enums import Category, Recurrence, Status, Currency
from uuid import UUID


class ObligationSingleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    title: str = Field(max_length=255)
    amount: Decimal
    currency: Currency
    category: Category
    recurrence: Recurrence | None
    next_payment_date: date
    status: Status
    created_at: datetime
    updated_at: datetime


class ObligationResponse(BaseModel):
    obligation: ObligationSingleResponse
    warning: str | None = Field(default=None)


class ObligationRequest(BaseModel):
    title: str = Field(max_length=255)
    amount: Decimal
    currency: Currency = Currency.RUB
    category: Category
    recurrence: Recurrence | None = None
    next_payment_date: date

    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError('Сумма должна быть положительной')

        return value.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError('Название не должно быть пустым')
        return value


class ObligationParamsQuery(BaseModel):
    category: Category | None = None
    status: Status | None = None


class DaysQuery(BaseModel):
    days: int = 7

    @field_validator('days')
    @classmethod
    def days_must_be_positive(cls, value: int) -> int:
        if value < 0:
            raise ValueError('Количество дней должно быть неотрицательным целым числом')

        return value


class ObligationRenewalAlerts(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    title: str = Field(max_length=255)
    next_payment_date: date
    amount: Decimal
    currency: Currency


class ObligationUpcomingResponse(BaseModel):
    obligations: list[ObligationSingleResponse]
    totals: dict[Currency, Decimal]
    renewal_alerts: list[ObligationRenewalAlerts]


class PaymentSingleResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    obligation_id: UUID
    amount: Decimal
    currency: Currency
    paid_at: datetime


class PaymentResponse(BaseModel):
    obligation: ObligationSingleResponse
    payment: PaymentSingleResponse


class PaymentRequest(BaseModel):
    obligation_id: UUID
    amount: Decimal
    currency: Currency
