from app.database import Base
from app.enums import Category, Recurrence, Status, Currency

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, Numeric, String, func, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency_enum"),
        default=Currency.RUB,
        server_default=text("'RUB'"),
        nullable=False,
    )

    category: Mapped[Category] = mapped_column(
        Enum(Category, name="category_enum"),
        nullable=False,
    )

    recurrence: Mapped[Recurrence | None] = mapped_column(
        Enum(Recurrence, name="recurrence_enum"),
        nullable=True,
    )

    next_payment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status_enum"),
        nullable=False,
        default=Status.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    payments: Mapped[list["Payment"]] = relationship(
        back_populates="obligation",
        cascade="all, delete-orphan",
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    obligation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("obligations.id"),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency_enum"),
        default=Currency.RUB,
        server_default=text("'RUB'"),
        nullable=False,
    )

    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    obligation: Mapped["Obligation"] = relationship(
        back_populates="payments",
    )