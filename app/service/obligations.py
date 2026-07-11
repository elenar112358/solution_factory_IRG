from datetime import date, datetime
from app.enums import Category, Recurrence, Status, Currency

from sqlalchemy.orm import Session

from app.schemas import (
    ObligationRequest,
    ObligationSingleResponse,
    ObligationResponse,
    ObligationQuery,
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

def get_obligations(db: Session, query_params: ObligationQuery) -> list[ObligationSingleResponse]:
    today = date.today()
    obligations_repository.set_lazy_expiry(db, today)
    db.commit()

    obligations = obligations_repository.get_obligations_by_params(db, query_params)

    return [ObligationSingleResponse.model_validate(obligation) for obligation in obligations]