from datetime import date, timedelta
from collections import defaultdict
from decimal import Decimal

from app.enums import Category, Recurrence, Status, Currency

from sqlalchemy.orm import Session

from app.schemas import (
    ObligationRequest,
    ObligationSingleResponse,
    ObligationResponse,
    ObligationParamsQuery,
    ObligationDaysQuery,
    ObligationUpcomingResponse,
    ObligationRenewalAlerts,
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


def get_upcoming_obligations(db: Session, query_days: ObligationDaysQuery) -> ObligationUpcomingResponse:
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
