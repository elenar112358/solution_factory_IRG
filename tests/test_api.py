from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
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


def test_add_obligation_success(db_session, client, obligation_request_success):
    response = client.post(
        "/api/v1/obligations/",
        json=obligation_request_success,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligation" in body
    assert "warning" in body

    assert body["warning"] is None
    assert body["obligation"]["title"] == obligation_request_success["title"]
    assert Decimal(body["obligation"]["amount"]) == Decimal(obligation_request_success["amount"])
    assert body["obligation"]["currency"] == obligation_request_success["currency"]
    assert body["obligation"]["category"] == obligation_request_success["category"]
    assert body["obligation"]["recurrence"] == obligation_request_success["recurrence"]
    assert body["obligation"]["next_payment_date"] == obligation_request_success["next_payment_date"]
    assert body["obligation"]["status"] == Status.ACTIVE.value

    created_at = datetime.fromisoformat(body["obligation"]["created_at"])
    updated_at = datetime.fromisoformat(body["obligation"]["updated_at"])

    assert isinstance(created_at, datetime)
    assert isinstance(updated_at, datetime)

    obligation = (
        db_session.query(Obligation)
        .filter_by(title=obligation_request_success["title"], status=Status.ACTIVE)
        .first()
    )

    assert obligation is not None
    assert obligation.amount == Decimal(obligation_request_success["amount"])

def test_add_obligation_with_expired_status(db_session, client, obligation_request_expired):
    response = client.post(
        "/api/v1/obligations/",
        json=obligation_request_expired,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligation" in body
    assert "warning" in body

    assert body["warning"] is None
    assert body["obligation"]["title"] == obligation_request_expired["title"]
    assert Decimal(body["obligation"]["amount"]) == Decimal(obligation_request_expired["amount"])
    assert body["obligation"]["currency"] == obligation_request_expired["currency"]
    assert body["obligation"]["category"] == obligation_request_expired["category"]
    assert body["obligation"]["recurrence"] == obligation_request_expired["recurrence"]
    assert body["obligation"]["next_payment_date"] == obligation_request_expired["next_payment_date"]
    assert body["obligation"]["status"] == Status.EXPIRED.value

    obligation = (
        db_session.query(Obligation)
        .filter_by(title=obligation_request_expired["title"], status=Status.EXPIRED)
        .first()
    )

    assert obligation is not None
    assert obligation.amount == Decimal(obligation_request_expired["amount"])

def test_add_obligation_duplicate_title_returns_warning(
        db_session,
        client,
        obligation_request_duplicate_1,
        obligation_request_duplicate_2,
):

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_1,
    )

    response_2 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_2,
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

    assert body_1["obligation"]["title"] == obligation_request_duplicate_1["title"]
    assert body_2["obligation"]["title"] == obligation_request_duplicate_2["title"]

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

def test_add_obligation_duplicate_title_returns_no_warning(
        db_session,
        client,
        obligation_request_duplicate_1,
        obligation_request_duplicate_2,
):

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_2,
    )

    response_2 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_1,
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

    assert body_1["obligation"]["title"] == obligation_request_duplicate_2["title"]
    assert body_2["obligation"]["title"] == obligation_request_duplicate_1["title"]

    assert body_1["obligation"]["status"] == Status.EXPIRED.value
    assert body_2["obligation"]["status"] == Status.ACTIVE.value

    obligation_1 = (
        db_session.query(Obligation)
        .filter_by(title=obligation_request_duplicate_2["title"], status=Status.EXPIRED)
        .first()
    )
    assert obligation_1 is not None

    obligation_2 = (
        db_session.query(Obligation)
        .filter_by(title=obligation_request_duplicate_1["title"], status=Status.ACTIVE)
        .first()
    )
    assert obligation_2 is not None

def test_get_obligations_success(
        db_session,
        client,
        obligation_request_success,
        obligation_request_expired,
):

    response_post = client.post(
        "/api/v1/obligations/",
        json=obligation_request_success,
    )
    assert response_post.status_code == 200, response_post.text

    # ==============================================

    query_params = {
        "category": Category.SUBSCRIPTION.value,
        "status": Status.EXPIRED.value
    }

    response = client.get(
        "/api/v1/obligations/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 0

    # ==============================================

    query_params = {
        "category": Category.SUBSCRIPTION.value,
    }

    response = client.get(
        "/api/v1/obligations/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    assert body[0]["title"] == obligation_request_success["title"]
    assert Decimal(body[0]["amount"]) == Decimal(obligation_request_success["amount"])
    assert body[0]["currency"] == obligation_request_success["currency"]
    assert body[0]["category"] == obligation_request_success["category"]
    assert body[0]["recurrence"] == obligation_request_success["recurrence"]
    assert body[0]["next_payment_date"] == obligation_request_success["next_payment_date"]
    assert body[0]["status"] == Status.ACTIVE.value

    # ==============================================

    response_post = client.post(
        "/api/v1/obligations/",
        json=obligation_request_expired,
    )
    assert response_post.status_code == 200, response_post.text

    query_params = {
        "status": Status.EXPIRED.value,
    }

    response = client.get(
        "/api/v1/obligations/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    assert body[0]["title"] == obligation_request_expired["title"]
    assert Decimal(body[0]["amount"]) == Decimal(obligation_request_expired["amount"])
    assert body[0]["currency"] == obligation_request_expired["currency"]
    assert body[0]["category"] == obligation_request_expired["category"]
    assert body[0]["recurrence"] == obligation_request_expired["recurrence"]
    assert body[0]["next_payment_date"] == obligation_request_expired["next_payment_date"]
    assert body[0]["status"] == Status.EXPIRED.value

def test_get_obligations_sorting(
        db_session,
        client,
        obligation_request_success,
        obligation_request_duplicate_2,
):

    response_post = client.post(
        "/api/v1/obligations/",
        json=obligation_request_success,
    )
    assert response_post.status_code == 200, response_post.text

    response_post = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_2,
    )
    assert response_post.status_code == 200, response_post.text

    query_params = {
        "category": Category.SUBSCRIPTION.value,
    }

    response = client.get(
        "/api/v1/obligations/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2

    date1 = date.fromisoformat(body[0]["next_payment_date"])
    date2 = date.fromisoformat(body[1]["next_payment_date"])

    assert date1 <= date2
    assert body[0]["category"] ==  body[1]["category"]


def test_get_obligations_lazy_expiry_to_expired(
        db_session,
        client,
        obligation_request_success,
        obligation_request_duplicate_2,
):
    payment_date = date.today() - timedelta(days=2)
    obligation = Obligation(
        title="Subscription_2",
        amount=1700.00,
        currency=Currency.EUR,
        category=Category.SUBSCRIPTION,
        recurrence=None,
        next_payment_date=payment_date,
        status=Status.ACTIVE,
    )
    db_session.add(obligation)
    db_session.flush()
    db_session.commit()

    query_params = {
        "category": Category.SUBSCRIPTION.value,
    }

    response = client.get(
        "/api/v1/obligations/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    assert body[0]["status"] == Status.EXPIRED.value

def test_get_obligations_lazy_expiry_stay_active(
        db_session,
        client,
        obligation_request_success,
        obligation_request_duplicate_2,
):

    payment_date = date.today() - timedelta(days=2)
    obligation = Obligation(
        title="Subscription_2",
        amount=1700.00,
        currency=Currency.EUR,
        category=Category.SUBSCRIPTION,
        recurrence=Recurrence.MONTHLY,
        next_payment_date=payment_date,
        status=Status.ACTIVE,
    )
    db_session.add(obligation)
    db_session.flush()
    db_session.commit()

    query_params = {
        "category": Category.SUBSCRIPTION.value,
    }

    response = client.get(
        "/api/v1/obligations/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    assert body[0]["status"] == Status.ACTIVE.value

def test_get_upcoming_obligations(
        db_session,
        client,
        obligation_request_success,
        obligation_request_duplicate_1,
        obligation_request_duplicate_2,
):

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_success,
    )

    response_2 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_1,
    )

    response_3 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_2,
    )

    assert response_1.status_code == 200, response_1.text
    assert response_2.status_code == 200, response_2.text
    assert response_3.status_code == 200, response_3.text

    # ===============================================

    days = 15
    query_params = {"days": days}
    response = client.get(
        "/api/v1/obligations/upcoming/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligations" in body
    assert "totals" in body
    assert "renewal_alerts" in body

    assert isinstance(body["obligations"], list)
    assert isinstance(body["totals"], dict)
    assert isinstance(body["renewal_alerts"], list)

    assert len(body["obligations"]) == 2
    payment_date = date.today() + timedelta(days=days)
    for obligation in body["obligations"]:
        body_date = date.fromisoformat(obligation["next_payment_date"])
        assert date.today() <= body_date <= payment_date

    assert body["totals"] == {
        Currency.RUB.value: "1000.00",
        Currency.EUR.value: "1000.00",
    }

    assert len(body["renewal_alerts"]) == 1
    for alerts in body["renewal_alerts"]:
        body_date = date.fromisoformat(alerts["next_payment_date"])
        assert date.today() <= body_date <= payment_date

    # ===============================================

    days = 3
    query_params = {"days": days}
    response = client.get(
        "/api/v1/obligations/upcoming/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligations" in body
    assert "totals" in body
    assert "renewal_alerts" in body

    assert isinstance(body["obligations"], list)
    assert isinstance(body["totals"], dict)
    assert isinstance(body["renewal_alerts"], list)

    assert len(body["obligations"]) == 0
    assert body["totals"] == {}
    assert len(body["renewal_alerts"]) == 0

# ===============================================

    query_params = {}
    response = client.get(
        "/api/v1/obligations/upcoming/",
        params=query_params,
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligations" in body
    assert "totals" in body
    assert "renewal_alerts" in body

    assert isinstance(body["obligations"], list)
    assert isinstance(body["totals"], dict)
    assert isinstance(body["renewal_alerts"], list)

    assert len(body["obligations"]) == 1
    payment_date = date.today() + timedelta(days=7)
    for obligation in body["obligations"]:
        body_date = date.fromisoformat(obligation["next_payment_date"])
        assert date.today() <= body_date <= payment_date

    assert body["totals"] == {
        Currency.RUB.value: "1000.00",
    }

    assert len(body["renewal_alerts"]) == 1
    for alerts in body["renewal_alerts"]:
        body_date = date.fromisoformat(alerts["next_payment_date"])
        assert date.today() <= body_date <= payment_date

def test_add_payment_active(
        db_session,
        client,
        obligation_request_success,
):

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_success,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}/pay"

    response = client.post(url_text)
    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligation" in body
    assert "payment" in body

    payment_date = date.fromisoformat(obligation_request_success["next_payment_date"]) + relativedelta(months=1)

    assert body["obligation"]["title"] == obligation_request_success["title"]
    assert Decimal(body["obligation"]["amount"]) == Decimal(obligation_request_success["amount"])
    assert body["obligation"]["currency"] == obligation_request_success["currency"]
    assert body["obligation"]["category"] == obligation_request_success["category"]
    assert body["obligation"]["recurrence"] == obligation_request_success["recurrence"]
    assert body["obligation"]["next_payment_date"] == payment_date.isoformat()
    assert body["obligation"]["status"] == Status.ACTIVE.value

    assert body["payment"]["obligation_id"] == str(id)
    assert Decimal(body["payment"]["amount"]) == Decimal(obligation_request_success["amount"])
    assert body["payment"]["currency"] == obligation_request_success["currency"]
    paid_at = datetime.fromisoformat(body["payment"]["paid_at"])
    assert paid_at.date() == date.today()

    payment = db_session.query(Payment).first()

    assert payment.obligation_id == id
    assert payment.amount == Decimal(obligation_request_success["amount"])
    assert payment.currency == obligation_request_success["currency"]

    paid_at = payment.paid_at
    assert isinstance(paid_at, datetime)
    assert paid_at.date() == date.today()


def test_add_payment_cancelled(
        db_session,
        client,
        obligation_request_duplicate_1,
):
    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_1,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}/pay"

    response = client.post(url_text)
    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligation" in body
    assert "payment" in body

    assert body["obligation"]["title"] == obligation_request_duplicate_1["title"]
    assert Decimal(body["obligation"]["amount"]) == Decimal(obligation_request_duplicate_1["amount"])
    assert body["obligation"]["currency"] == obligation_request_duplicate_1["currency"]
    assert body["obligation"]["category"] == obligation_request_duplicate_1["category"]
    assert body["obligation"]["recurrence"] == obligation_request_duplicate_1["recurrence"]
    assert body["obligation"]["status"] == Status.CANCELLED.value

    assert body["payment"]["obligation_id"] == str(id)
    assert Decimal(body["payment"]["amount"]) == Decimal(obligation_request_duplicate_1["amount"])
    assert body["payment"]["currency"] == obligation_request_duplicate_1["currency"]
    paid_at = datetime.fromisoformat(body["payment"]["paid_at"])
    assert paid_at.date() == date.today()

    payment = db_session.query(Payment).first()

    assert payment.obligation_id == id
    assert payment.amount == Decimal(obligation_request_duplicate_1["amount"])
    assert payment.currency == obligation_request_duplicate_1["currency"]

    paid_at = payment.paid_at
    assert isinstance(paid_at, datetime)
    assert paid_at.date() == date.today()

def test_add_payment_not_success(
        db_session,
        client,
        obligation_request_duplicate_1,
):
    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_duplicate_1,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}/pay"

    response = client.post(url_text)
    assert response.status_code == 200, response.text

    response = client.post(url_text)
    assert response.status_code == 422, response.text

def test_add_payment_monthly(
        db_session,
        client,
        obligation_request_monthly,
):

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_monthly,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}/pay"

    response = client.post(url_text)
    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligation" in body
    assert "payment" in body

    assert body["obligation"]["title"] == obligation_request_monthly["title"]
    assert Decimal(body["obligation"]["amount"]) == Decimal(obligation_request_monthly["amount"])
    assert body["obligation"]["currency"] == obligation_request_monthly["currency"]
    assert body["obligation"]["category"] == obligation_request_monthly["category"]
    assert body["obligation"]["recurrence"] == obligation_request_monthly["recurrence"]
    assert body["obligation"]["next_payment_date"] == "2027-02-28"
    assert body["obligation"]["status"] == Status.ACTIVE.value

def test_add_payment_quarterly(
        db_session,
        client,
        obligation_request_monthly,
):

    obligation_request_quarterly = obligation_request_monthly.copy()
    obligation_request_quarterly["recurrence"] = Recurrence.QUARTERLY.value

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_quarterly,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}/pay"

    response = client.post(url_text)
    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligation" in body
    assert "payment" in body

    assert body["obligation"]["title"] == obligation_request_quarterly["title"]
    assert Decimal(body["obligation"]["amount"]) == Decimal(obligation_request_quarterly["amount"])
    assert body["obligation"]["currency"] == obligation_request_quarterly["currency"]
    assert body["obligation"]["category"] == obligation_request_quarterly["category"]
    assert body["obligation"]["recurrence"] == obligation_request_quarterly["recurrence"]
    assert body["obligation"]["next_payment_date"] == "2027-04-30"
    assert body["obligation"]["status"] == Status.ACTIVE.value

def test_add_payment_yearly(
        db_session,
        client,
        obligation_request_monthly,
):

    obligation_request_yearly = obligation_request_monthly.copy()
    obligation_request_yearly["recurrence"] = Recurrence.YEARLY.value
    obligation_request_yearly["next_payment_date"] = "2028-02-29"

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_yearly,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}/pay"

    response = client.post(url_text)
    assert response.status_code == 200, response.text

    body = response.json()
    assert "obligation" in body
    assert "payment" in body

    assert body["obligation"]["title"] == obligation_request_yearly["title"]
    assert Decimal(body["obligation"]["amount"]) == Decimal(obligation_request_yearly["amount"])
    assert body["obligation"]["currency"] == obligation_request_yearly["currency"]
    assert body["obligation"]["category"] == obligation_request_yearly["category"]
    assert body["obligation"]["recurrence"] == obligation_request_yearly["recurrence"]
    assert body["obligation"]["next_payment_date"] == "2029-02-28"
    assert body["obligation"]["status"] == Status.ACTIVE.value

def test_cancel_obligation_success(
        db_session,
        client,
        obligation_request_success,
):

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_success,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}/cancel"

    response = client.patch(url_text)
    assert response.status_code == 200, response.text

    body = response.json()

    assert body["title"] == obligation_request_success["title"]
    assert Decimal(body["amount"]) == Decimal(obligation_request_success["amount"])
    assert body["currency"] == obligation_request_success["currency"]
    assert body["category"] == obligation_request_success["category"]
    assert body["recurrence"] == obligation_request_success["recurrence"]
    assert body["status"] == Status.CANCELLED.value

    db_session.refresh(obligation)
    obligation = (
        db_session.query(Obligation)
        .filter_by(id=id)
        .first()
    )

    assert obligation is not None
    assert obligation.status == Status.CANCELLED.value

def test_cancel_obligation_not_success(
        db_session,
        client,
        obligation_request_expired,
):

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_expired,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}/cancel"

    response = client.patch(url_text)
    assert response.status_code == 422, response.text

    db_session.refresh(obligation)
    obligation = (
        db_session.query(Obligation)
        .filter_by(id=id)
        .first()
    )

    assert obligation is not None
    assert obligation.status == Status.EXPIRED.value

def test_delete_obligation(
        db_session,
        client,
        obligation_request_expired,
):

    response_1 = client.post(
        "/api/v1/obligations/",
        json=obligation_request_expired,
    )

    assert response_1.status_code == 200, response_1.text

    obligation = db_session.query(Obligation).first()
    id = obligation.id
    url_text = f"/api/v1/obligations/{str(id)}"

    response = client.delete(url_text)
    assert response.status_code == 204, response.text

    obligation = (
        db_session.query(Obligation)
        .filter_by(id=id)
        .first()
    )

    assert obligation is None
