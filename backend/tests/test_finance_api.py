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

