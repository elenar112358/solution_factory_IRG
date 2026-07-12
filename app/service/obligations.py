from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from app.enums import Category, Recurrence, Status, Currency
from app.models import Obligation, Payment

from sqlalchemy.orm import Session
from fastapi import HTTPException

# from app.event_manager import broadcaster

from app.schemas import (
    ObligationRequest,
    ObligationSingleResponse,
    ObligationResponse,
    ObligationParamsQuery,
    DaysQuery,
    ObligationUpcomingResponse,
    ObligationRenewalAlerts,
    PaymentResponse,
    PaymentSingleResponse,
)
from app.repository import obligations as obligations_repository


def add_obligation(db: Session, obligation: ObligationRequest) -> ObligationResponse:
    today = date.today()
    if obligation.next_payment_date < today:
        status = Status.EXPIRED
    else:
        status = Status.ACTIVE

    warning = None
    if obligations_repository.is_obligation_exist(db, obligation.title):
        warning = "Активное обязательство с таким названием уже существует"

    created_obligation = obligations_repository.create_obligation(
        db=db,
        title=obligation.title,
        amount=obligation.amount,
        category=obligation.category,
        status=status,
        next_payment_date=obligation.next_payment_date,
        recurrence=obligation.recurrence,
        currency=obligation.currency,
    )
    db.commit()
    db.refresh(created_obligation)

    obligation_response = ObligationSingleResponse.model_validate(created_obligation)

    return ObligationResponse(
        obligation=obligation_response,
        warning=warning,
    )


def get_obligations(db: Session, query_params: ObligationParamsQuery) -> list[ObligationSingleResponse]:
    today = date.today()
    obligations_repository.set_lazy_expiry(db, today)
    db.commit()

    obligations = obligations_repository.get_obligations_by_params(db, query_params)

    return [ObligationSingleResponse.model_validate(obligation) for obligation in obligations]


def get_upcoming_obligations(db: Session, query_days: DaysQuery) -> ObligationUpcomingResponse:
    today = date.today()
    end_date = today + timedelta(days=query_days.days)

    upcoming_obligations = obligations_repository.get_upcoming_obligations(db, today, end_date)

    totals = defaultdict(Decimal)
    for obligation in upcoming_obligations:
        totals[obligation.currency] += obligation.amount

    renewal_alerts = obligations_repository.get_renewal_alerts(db, today, end_date)

    return ObligationUpcomingResponse(
        obligations=[ObligationSingleResponse.model_validate(obligation) for obligation in upcoming_obligations],
        totals=dict(totals),
        renewal_alerts=[ObligationRenewalAlerts.model_validate(alert) for alert in renewal_alerts]
    )

def check_obligation(obligation: Obligation, obligation_id: UUID) -> None:
    if not obligation:
        raise HTTPException(
            status_code=404,
            detail=f"Обязательство с id = '{obligation_id}' не найдено"
        )

    if obligation.status != Status.ACTIVE:
        raise HTTPException(
            status_code=422,
            detail=f"Обязательство с id = '{obligation_id}' не активно"
        )

def add_payment(db: Session, obligation_id: UUID) -> PaymentResponse:
    obligation = obligations_repository.get_obligation_by_id(db, obligation_id)
    check_obligation(obligation, obligation_id)

    payment = obligations_repository.create_payment(
        db=db,
        obligation_id=obligation_id,
        amount=obligation.amount,
        currency=obligation.currency,
    )

    if obligation.recurrence is None:
        obligations_repository.cancel_obligation(db, obligation.id)
    else:
        next_payment_date = calculate_next_payment_date(obligation)
        obligations_repository.set_new_payment_date(db, obligation.id, next_payment_date)

    db.commit()
    db.refresh(payment)
    db.refresh(obligation)

    return PaymentResponse(
        obligation=ObligationSingleResponse.model_validate(obligation),
        payment=PaymentSingleResponse.model_validate(payment),
    )

def calculate_next_payment_date(obligation: Obligation) -> date:
    next_payment_date = obligation.next_payment_date

    if obligation.recurrence == Recurrence.MONTHLY:
        return next_payment_date + relativedelta(months=1)

    if obligation.recurrence == Recurrence.QUARTERLY:
        return next_payment_date + relativedelta(months=3)

    if obligation.recurrence == Recurrence.YEARLY:
        return next_payment_date + relativedelta(years=1)

    raise ValueError(f"Неизвестный период: {obligation.recurrence}")

def cancel_obligation(db: Session, obligation_id: UUID) -> ObligationSingleResponse:
    obligation = obligations_repository.get_obligation_by_id(db, obligation_id)
    check_obligation(obligation, obligation_id)
    obligations_repository.cancel_obligation(db, obligation.id)

    db.commit()
    db.refresh(obligation)

    return ObligationSingleResponse.model_validate(obligation)

def delete_obligation(db: Session, obligation_id: UUID) -> None:
    obligation = obligations_repository.get_obligation_by_id(db, obligation_id)

    if not obligation:
        raise HTTPException(
            status_code=404,
            detail=f"Обязательство с id = '{obligation_id}' не найдено"
        )

    obligations_repository.delete_obligation(db, obligation_id)
    db.commit()

    # broadcaster.broadcast(
    #     {
    #         "type": "obligation_deleted",
    #         "id": str(obligation_id),
    #     }
    # )

