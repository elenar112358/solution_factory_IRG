from decimal import Decimal

from sqlalchemy.orm import Session
from datetime import date, datetime

from app.enums import Category, Recurrence, Status, Currency
from app.models import Obligation
from app.schemas import ObligationQuery


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
        query_params: ObligationQuery,
) -> list[Obligation]:

    filters = []

    for field_name, value in query_params.model_dump(exclude_none=True).items():
        filters.append(getattr(Obligation, field_name) == value)

    query = db.query(Obligation)
    query = query.filter(*filters)
    query = query.order_by(Obligation.next_payment_date)

    return query.all()

# Бизнес-правило (lazy expiry). Перед формированием ответа сервис переводит все записи со статусом
# active и next_payment_date < today в статус expired. Рекуррентные обязательства (recurrence != null) под это
# правило не попадают: если пользователь не нажал «Оплачено», дата просто устарела, но подписка не
# прекратилась. Для них статус остаётся active. Обоснуй этот выбор в README.

def set_lazy_expiry(db: Session, expiration_date: date) -> None:
    db.query(Obligation).filter(
        Obligation.next_payment_date < expiration_date,
        Obligation.status == Status.ACTIVE,
        Obligation.recurrence.is_(None),
    ).update(
        {Obligation.status: Status.EXPIRED},
        synchronize_session=False,
    )

