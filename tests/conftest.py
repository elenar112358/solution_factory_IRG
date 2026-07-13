from typing import Generator, Any
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base
from app.dependency import get_db
from app.main import app
from app.enums import Category, Recurrence, Status, Currency

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


def get_test_db() -> Generator[Session, None, None]:
    with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = get_test_db

@pytest.fixture()
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    with TestSessionLocal() as session:
        yield session

@pytest.fixture
def obligation_request_success() -> dict[str, Any]:
    payment_date = date.today() + timedelta(days=5)

    obligation_request = {
        "title": "Subscription_1",
        "amount": 1000.00,
        "currency": Currency.RUB.value,
        "category": Category.SUBSCRIPTION.value,
        "recurrence": Recurrence.MONTHLY.value,
        "next_payment_date": payment_date.isoformat(),
    }

    return obligation_request

@pytest.fixture
def obligation_request_expired() -> dict[str, Any]:
    payment_date = date.today() - timedelta(days=2)

    obligation_request = {
        "title": "Subscription_1",
        "amount": 1000.00,
        "currency": Currency.RUB.value,
        "category": Category.WARRANTY.value,
        "recurrence": None,
        "next_payment_date": payment_date.isoformat(),
    }

    return obligation_request

@pytest.fixture
def obligation_request_duplicate_1() -> dict[str, Any]:
    payment_date = date.today() + timedelta(days=12)

    obligation_request = {
        "title": "Subscription_1",
        "amount": 1000.00,
        "currency": Currency.EUR.value,
        "category": Category.BILL.value,
        "recurrence": None,
        "next_payment_date": payment_date.isoformat(),
    }

    return obligation_request

@pytest.fixture
def obligation_request_duplicate_2() -> dict[str, Any]:
    payment_date = date.today() - timedelta(days=2)

    obligation_request = {
        "title": "subscription_1",
        "amount": 500.00,
        "currency": Currency.USD.value,
        "category": Category.SUBSCRIPTION.value,
        "recurrence": None,
        "next_payment_date": payment_date.isoformat(),
    }

    return obligation_request

@pytest.fixture
def obligation_request_monthly() -> dict[str, Any]:
    obligation_request = {
        "title": "Subscription_1",
        "amount": 1000.00,
        "currency": Currency.RUB.value,
        "category": Category.SUBSCRIPTION.value,
        "recurrence": Recurrence.MONTHLY.value,
        "next_payment_date": "2027-01-31",
    }

    return obligation_request