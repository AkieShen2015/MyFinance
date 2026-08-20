import asyncio
from collections.abc import Generator
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.services.seed import seed_mock_data


def test_dashboard_analytics_are_consistent_and_fill_months(session: Session) -> None:
    asyncio.run(seed_mock_data(session))

    def override_database() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_database
    params = {"date_from": "2026-05-01", "date_to": "2026-08-31"}
    try:
        client = TestClient(app)
        summary_response = client.get("/api/dashboard/summary", params=params)
        categories_response = client.get(
            "/api/dashboard/expenses-by-category", params=params
        )
        trend_response = client.get("/api/dashboard/income-vs-expenses", params=params)
        overview_response = client.get("/api/overview")
        accounts = client.get("/api/accounts").json()
        selected_params = [
            ("date_from", params["date_from"]),
            ("date_to", params["date_to"]),
            ("account_id", accounts[0]["id"]),
            ("account_id", accounts[1]["id"]),
        ]
        selected_summary_response = client.get(
            "/api/dashboard/summary", params=selected_params
        )
        selected_categories_response = client.get(
            "/api/dashboard/expenses-by-category", params=selected_params
        )
        selected_trend_response = client.get(
            "/api/dashboard/income-vs-expenses", params=selected_params
        )
    finally:
        app.dependency_overrides.clear()

    assert summary_response.status_code == 200
    assert categories_response.status_code == 200
    assert trend_response.status_code == 200

    summary = summary_response.json()
    categories = categories_response.json()
    trend = trend_response.json()
    total_income = Decimal(summary["total_income"])
    total_expenses = Decimal(summary["total_expenses"])
    assert total_income > 0
    assert total_expenses > 0
    assert Decimal(summary["net_cash_flow"]) == total_income - total_expenses
    assert summary["total_account_balance"] == overview_response.json()["total_balance"]

    assert sum((Decimal(item["amount"]) for item in categories), Decimal("0")) == total_expenses
    assert categories == sorted(
        categories,
        key=lambda item: (-Decimal(item["amount"]), item["category"].casefold()),
    )
    assert Decimal(categories[0]["percentage"]) > 0

    assert [item["month"] for item in trend] == [
        "2026-05-01",
        "2026-06-01",
        "2026-07-01",
        "2026-08-01",
    ]
    assert sum((Decimal(item["income"]) for item in trend), Decimal("0")) == total_income
    assert sum((Decimal(item["expenses"]) for item in trend), Decimal("0")) == total_expenses

    assert selected_summary_response.status_code == 200
    assert selected_categories_response.status_code == 200
    assert selected_trend_response.status_code == 200
    selected_summary = selected_summary_response.json()
    selected_categories = selected_categories_response.json()
    selected_trend = selected_trend_response.json()
    expected_selected_balance = sum(
        (Decimal(account["current_balance"]) for account in accounts[:2]),
        Decimal("0"),
    )
    assert Decimal(selected_summary["total_account_balance"]) == expected_selected_balance
    assert Decimal(selected_summary["total_expenses"]) <= total_expenses
    assert sum(
        (Decimal(item["amount"]) for item in selected_categories), Decimal("0")
    ) == Decimal(selected_summary["total_expenses"])
    assert sum(
        (Decimal(item["income"]) for item in selected_trend), Decimal("0")
    ) == Decimal(selected_summary["total_income"])


def test_dashboard_rejects_an_inverted_period(session: Session) -> None:
    asyncio.run(seed_mock_data(session))

    def override_database() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_database
    try:
        response = TestClient(app).get(
            "/api/dashboard/summary",
            params={"date_from": "2026-08-31", "date_to": "2026-08-01"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"] == "date_from must not be after date_to"


def test_dashboard_rejects_accounts_outside_the_user_scope(session: Session) -> None:
    asyncio.run(seed_mock_data(session))

    def override_database() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_database
    try:
        response = TestClient(app).get(
            "/api/dashboard/summary",
            params={
                "account_id": str(uuid4()),
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Account not found"


def test_advanced_analytics_are_ranked_and_ai_payload_is_aggregated(
    session: Session,
) -> None:
    asyncio.run(seed_mock_data(session))

    def override_database() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_database
    try:
        response = TestClient(app).get(
            "/api/analytics/report",
            params={"date_from": "2026-05-01", "date_to": "2026-08-31"},
        )
        year_comparison_response = TestClient(app).get(
            "/api/analytics/report",
            params={
                "date_from": "2026-01-01",
                "date_to": "2026-04-01",
                "comparison": "previous_year",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert year_comparison_response.status_code == 200
    year_comparison = year_comparison_response.json()
    assert year_comparison["previous_date_from"] == "2025-01-01"
    assert year_comparison["previous_date_to"] == "2025-04-01"
    report = response.json()
    assert report["previous_date_to"] == "2026-04-30"
    assert report["previous_date_from"] == "2025-12-29"
    assert Decimal(report["expenses"]["current"]) > 0
    assert report["top_merchants"] == sorted(
        report["top_merchants"],
        key=lambda item: (-Decimal(item["amount"]), item["merchant"]),
    )
    assert report["category_trends"]
    assert len(report["recurring_payments"]) > 8
    assert all(len(item["monthly"]) == 4 for item in report["category_trends"])
    assert all(
        sum((Decimal(point["amount"]) for point in item["monthly"]), Decimal("0"))
        == Decimal(item["current_amount"])
        for item in report["category_trends"]
    )
    assert report["insights"] == sorted(
        report["insights"],
        key=lambda item: (-Decimal(item["impact_amount"]), -Decimal(item["confidence"])),
    )
    assert set(report["ai_payload"]) == {
        "period_start",
        "period_end",
        "expense_change_amount",
        "expense_change_percentage",
        "top_category_changes",
        "recurring_total",
        "anomaly_count",
    }
    serialized_payload = str(report["ai_payload"]).lower()
    assert "description" not in serialized_payload
    assert "account" not in serialized_payload
