from decimal import Decimal

from sqlalchemy.orm import Session
from datetime import date

from app.enums import Category, Recurrence, Status, Currency
from app.models import Obligation
from app.schemas import ObligationParamsQuery


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

def get_obligations_by_params(
        db: Session,
        query_params: ObligationParamsQuery,
) -> list[Obligation]:

    filters = []

    for field_name, value in query_params.model_dump(exclude_none=True).items():
        filters.append(getattr(Obligation, field_name) == value)

    query = db.query(Obligation)
    query = query.filter(*filters)
    query = query.order_by(Obligation.next_payment_date)

    return query.all()

def set_lazy_expiry(db: Session, expiration_date: date) -> None:
    db.query(Obligation).filter(
        Obligation.next_payment_date < expiration_date,
        Obligation.status == Status.ACTIVE,
        Obligation.recurrence.is_(None),
    ).update(
        {Obligation.status: Status.EXPIRED},
        synchronize_session=False,
    )

def get_upcoming_obligations(
        db: Session,
        start_date: date,
        end_date: date,
) -> list[Obligation]:

    query = db.query(Obligation)
    query = query.filter(
        Obligation.next_payment_date >= start_date,
        Obligation.next_payment_date <= end_date,
        Obligation.status != Status.CANCELLED,
    )
    query = query.order_by(Obligation.next_payment_date)

    return query.all()

def get_renewal_alerts(
        db: Session,
        start_date: date,
        end_date: date,
) -> list[Obligation]:

    query = db.query(Obligation)
    query = query.filter(
        Obligation.next_payment_date >= start_date,
        Obligation.next_payment_date <= end_date,
        Obligation.status != Status.CANCELLED,
        Obligation.category == Category.SUBSCRIPTION,
        Obligation.recurrence.is_not(None)
    )
    query = query.order_by(Obligation.next_payment_date)

    return query.all()
