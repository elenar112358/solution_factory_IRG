from decimal import Decimal

from sqlalchemy.orm import Session
from datetime import date, datetime

from app.enums import Category, Recurrence, Status, Currency
from app.models import Obligation


def is_obligation_exist(db: Session, title: str) -> bool:
    obligation = db.query(Obligation).filter(
        Obligation.title == title,
        Obligation.status == Status.ACTIVE,
    ).first()

    return obligation is not None

def create_obligation(
        db: Session,
        title: str,
        amount: Decimal,
        category: Category,
        status: Status,
        next_payment_date: date,
        recurrence: Recurrence | None = None,
        currency: Currency = Currency.RUB,
) -> Obligation:

    obligation = Obligation(
        title=title,
        amount=amount,
        currency=currency,
        category=category,
        recurrence=recurrence,
        next_payment_date=next_payment_date,
        status=status,
    )
    db.add(obligation)
    db.flush()
    return obligation