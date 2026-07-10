from datetime import date, datetime
from app.enums import Category, Recurrence, Status, Currency

from sqlalchemy.orm import Session

from app.schemas import ObligationRequest, ObligationResponse, ObligationFullResponse
from app.repository import obligations as obligations_repository


def add_obligation(db: Session, obligation: ObligationRequest) -> ObligationFullResponse:
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

    obligation_response = ObligationResponse.model_validate(created_obligation)

    return ObligationFullResponse(
        obligation=obligation_response,
        warning=warning,
    )