from decimal import Decimal
from datetime import date, datetime, timedelta
from app.models import Obligation, Payment
from app.enums import Category, Recurrence, Status, Currency
from app.schemas import (
    ObligationSingleResponse,
    ObligationRequest,
    ObligationResponse,
    ObligationParamsQuery,
    DaysQuery,
    ObligationUpcomingResponse,
    PaymentResponse,
)


def test_add_obligation_success(db_session, client):
    payment_date = date.today() + timedelta(days=5)
    obligation_request = {
        "title": "Subscription_1",
        "amount": 1000.00,
        "currency": Currency.RUB.value,
        "category": Category.SUBSCRIPTION.value,
        "recurrence": Recurrence.MONTHLY.value,
        "next_payment_date": payment_date.isoformat(),
    }

    response = client.post(
        "/api/v1/obligations/",
        json=obligation_request,
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert "obligation" in body
    assert "warning" in body

    assert body["warning"] is None
    assert body["obligation"]["title"] == "Subscription_1"
    assert Decimal(body["obligation"]["amount"]) == Decimal("1000")
    assert body["obligation"]["currency"] == Currency.RUB.value
    assert body["obligation"]["category"] == Category.SUBSCRIPTION.value
    assert body["obligation"]["recurrence"] == Recurrence.MONTHLY.value
    assert body["obligation"]["next_payment_date"] == payment_date.isoformat()
    assert body["obligation"]["status"] == Status.ACTIVE

    created_at = datetime.fromisoformat(body["obligation"]["created_at"])
    updated_at = datetime.fromisoformat(body["obligation"]["updated_at"])

    assert isinstance(created_at, datetime)
    assert isinstance(updated_at, datetime)

    obligation = (
        db_session.query(Obligation)
        .filter_by(title="Subscription_1", status=Status.ACTIVE)
        .first()
    )

    assert obligation is not None
    assert obligation.amount == Decimal("1000.00")

def test_add_obligation_with_expired_status(db_session, client):
    payment_date = date.today() - timedelta(days=2)
    obligation_request = {
        "title": "Subscription_1",
        "amount": 1000.00,
        "currency": Currency.RUB.value,
        "category": Category.WARRANTY.value,
        "recurrence": None,
        "next_payment_date": payment_date.isoformat(),
    }

    response = client.post(
        "/api/v1/obligations/",
        json=obligation_request,
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert "obligation" in body
    assert "warning" in body

    assert body["warning"] is None
    assert body["obligation"]["title"] == "Subscription_1"
    assert Decimal(body["obligation"]["amount"]) == Decimal("1000")
    assert body["obligation"]["currency"] == Currency.RUB.value
    assert body["obligation"]["category"] == Category.WARRANTY.value
    assert body["obligation"]["recurrence"] is None
    assert body["obligation"]["next_payment_date"] == payment_date.isoformat()
    assert body["obligation"]["status"] == Status.EXPIRED.value

    obligation = (
        db_session.query(Obligation)
        .filter_by(title="Subscription_1", status=Status.EXPIRED)
        .first()
    )

    assert obligation is not None
    assert obligation.amount == Decimal("1000.00")

def test_add_obligation_duplicate_title_returns_warning_before(db_session, client):
    payment_date = date.today() + timedelta(days=2)
    obligation_request_1 = {
        "title": "Subscription_1",
        "amount": 1000.00,
        "currency": Currency.RUB.value,
        "category": Category.WARRANTY.value,
        "recurrence": None,
        "next_payment_date": payment_date.isoformat(),
    }

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_1,
    )

    payment_date = date.today() - timedelta(days=2)
    obligation_request_2 = {
        "title": "subscription_1",
        "amount": 500.00,
        "currency": Currency.USD.value,
        "category": Category.SUBSCRIPTION.value,
        "recurrence": None,
        "next_payment_date": payment_date.isoformat(),
    }

    response_2 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_2,
    )

    assert response_1.status_code == 200, response_1.text
    assert response_2.status_code == 200, response_2.text

    body_1 = response_1.json()
    assert "obligation" in body_1
    assert "warning" in body_1

    body_2 = response_2.json()
    assert "obligation" in body_2
    assert "warning" in body_2

    obligations = (
        db_session.query(Obligation)
        .all()
    )
    assert len(obligations) == 2

    assert body_1["warning"] is None
    assert body_2["warning"] == "Активное обязательство с таким названием уже существует"

    assert body_1["obligation"]["title"] == "Subscription_1"
    assert body_2["obligation"]["title"] == "subscription_1"

    assert body_1["obligation"]["status"] == Status.ACTIVE.value
    assert body_2["obligation"]["status"] == Status.EXPIRED.value

    obligation_1 = (
        db_session.query(Obligation)
        .filter_by(title="Subscription_1", status=Status.ACTIVE)
        .first()
    )
    assert obligation_1 is not None

    obligation_2 = (
        db_session.query(Obligation)
        .filter_by(title="subscription_1", status=Status.EXPIRED)
        .first()
    )
    assert obligation_2 is not None

def test_add_obligation_duplicate_title_returns_warning_after(db_session, client):
    payment_date = date.today() - timedelta(days=2)
    obligation_request_1 = {
        "title": "Subscription_1",
        "amount": 1000.00,
        "currency": Currency.RUB.value,
        "category": Category.WARRANTY.value,
        "recurrence": None,
        "next_payment_date": payment_date.isoformat(),
    }

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_1,
    )

    payment_date = date.today() + timedelta(days=2)
    obligation_request_2 = {
        "title": "subscription_1",
        "amount": 500.00,
        "currency": Currency.USD.value,
        "category": Category.SUBSCRIPTION.value,
        "recurrence": None,
        "next_payment_date": payment_date.isoformat(),
    }

    response_2 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_2,
    )

    assert response_1.status_code == 200, response_1.text
    assert response_2.status_code == 200, response_2.text

    body_1 = response_1.json()
    assert "obligation" in body_1
    assert "warning" in body_1

    body_2 = response_2.json()
    assert "obligation" in body_2
    assert "warning" in body_2

    obligations = (
        db_session.query(Obligation)
        .all()
    )
    assert len(obligations) == 2

    assert body_1["warning"] is None
    assert body_2["warning"] is None

    assert body_1["obligation"]["title"] == "Subscription_1"
    assert body_2["obligation"]["title"] == "subscription_1"

    assert body_1["obligation"]["status"] == Status.EXPIRED.value
    assert body_2["obligation"]["status"] == Status.ACTIVE.value

    obligation_1 = (
        db_session.query(Obligation)
        .filter_by(title="Subscription_1", status=Status.EXPIRED)
        .first()
    )
    assert obligation_1 is not None

    obligation_2 = (
        db_session.query(Obligation)
        .filter_by(title="subscription_1", status=Status.ACTIVE)
        .first()
    )
    assert obligation_2 is not None