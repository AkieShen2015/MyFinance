import asyncio
from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.services.seed import seed_mock_data


def test_seeded_finance_data_is_available_without_sensitive_raw_data(session: Session) -> None:
    asyncio.run(seed_mock_data(session))

    def override_database() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_database
    try:
        client = TestClient(app)
        overview = client.get("/api/overview")
        accounts = client.get("/api/accounts")
        transactions = client.get("/api/transactions?limit=5")
        categories = client.get("/api/categories")
    finally:
        app.dependency_overrides.clear()

    assert overview.status_code == 200
    assert overview.json()["account_count"] == 3
    assert overview.json()["transaction_count"] > 100

    assert accounts.status_code == 200
    assert len(accounts.json()) == 3
    assert all("external_account_id" not in item for item in accounts.json())

    assert transactions.status_code == 200
    assert len(transactions.json()["items"]) == 5
    assert all("raw_data" not in item for item in transactions.json()["items"])

    assert categories.status_code == 200
    assert len(categories.json()) > 10


def test_transaction_search_category_update_and_tags(session: Session) -> None:
    asyncio.run(seed_mock_data(session))

    def override_database() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = override_database
    try:
        client = TestClient(app)
        search = client.get("/api/transactions?search=woolworths&limit=5")
        transaction = search.json()["items"][0]
        categories = client.get("/api/categories").json()
        other = next(item for item in categories if item["name"] == "Other")

        category_update = client.patch(
            f"/api/transactions/{transaction['id']}/category",
            json={"category_id": other["id"], "apply_to_similar": True},
        )
        tag_update = client.patch(
            f"/api/transactions/{transaction['id']}/tags",
            json={"tags": ["reviewed", "household", "reviewed"]},
        )
        refreshed = client.get("/api/transactions?search=woolworths&limit=5")
    finally:
        app.dependency_overrides.clear()

    assert search.status_code == 200
    assert search.json()["total"] == 48
    assert category_update.status_code == 204
    assert tag_update.status_code == 204
    changed = next(item for item in refreshed.json()["items"] if item["id"] == transaction["id"])
    assert changed["category_id"] == other["id"]
    assert changed["tags"] == ["household", "reviewed"]
