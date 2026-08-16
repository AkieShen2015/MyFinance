import asyncio
from collections.abc import Generator
from decimal import Decimal

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
        transaction_detail = client.get(
            f"/api/transactions/{transactions.json()['items'][0]['id']}"
        )
        anz_institution_id = next(
            item["institution_id"]
            for item in accounts.json()
            if item["institution_name"] == "ANZ"
        )
        anz_transactions = client.get(
            f"/api/transactions?institution_id={anz_institution_id}&limit=100"
        )
        categories = client.get("/api/categories")
        account_id = accounts.json()[0]["id"]
        restaurant_alias = client.post(
            "/api/categories",
            json={"account_id": account_id, "name": "Restaurant", "type": "expense"},
        )
        custom_category = client.post(
            "/api/categories",
            json={"account_id": account_id, "name": "Hobbies", "type": "expense"},
        )
        filtered_transactions = client.get(
            "/api/transactions",
            params={
                "account_id": account_id,
                "amount_max": "-1",
                "amount_min": "-500",
                "date_from": "2026-08-01",
                "date_to": "2026-08-31",
                "limit": 100,
                "sort_by": "amount",
                "sort_order": "asc",
                "transaction_type": "expense",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert overview.status_code == 200
    assert overview.json()["account_count"] == 15
    assert overview.json()["transaction_count"] > 100

    assert accounts.status_code == 200
    assert len(accounts.json()) == 15
    assert all("institution_id" in item for item in accounts.json())
    assert all("external_account_id" not in item for item in accounts.json())

    assert transactions.status_code == 200
    assert len(transactions.json()["items"]) == 5
    assert all("raw_data" not in item for item in transactions.json()["items"])
    assert transaction_detail.status_code == 200
    assert transaction_detail.json()["id"] == transactions.json()["items"][0]["id"]
    assert "raw_data" not in transaction_detail.json()
    assert anz_transactions.status_code == 200
    assert anz_transactions.json()["total"] > 0
    assert all(
        item["institution_name"] == "ANZ"
        for item in anz_transactions.json()["items"]
    )

    assert categories.status_code == 200
    assert len(categories.json()) > 10
    category_names = {item["name"] for item in categories.json()}
    assert {"Food & Restaurant", "Pet"}.issubset(category_names)
    assert category_names.isdisjoint({"Restaurants", "Vet"})
    assert restaurant_alias.status_code == 200
    assert restaurant_alias.json()["name"] == "Food & Restaurant"
    assert restaurant_alias.json()["account_id"] is None
    assert custom_category.status_code == 200
    assert custom_category.json()["name"] == "Hobbies"
    assert custom_category.json()["account_id"] == account_id
    assert filtered_transactions.status_code == 200
    filtered_items = filtered_transactions.json()["items"]
    assert filtered_items
    assert all(item["account_id"] == account_id for item in filtered_items)
    assert all(item["transaction_type"] == "expense" for item in filtered_items)
    filtered_amounts = [Decimal(item["amount"]) for item in filtered_items]
    assert filtered_amounts == sorted(filtered_amounts)
    assert all(Decimal("-500") <= amount <= Decimal("-1") for amount in filtered_amounts)


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
        different_account_id = next(
            item["id"]
            for item in client.get("/api/accounts").json()
            if item["id"] != transaction["account_id"]
        )
        different_account_category = client.post(
            "/api/categories",
            json={
                "account_id": different_account_id,
                "name": "Different account only",
                "type": "expense",
            },
        ).json()
        cross_account_update = client.patch(
            f"/api/transactions/{transaction['id']}/category",
            json={
                "category_id": different_account_category["id"],
                "apply_to_similar": False,
            },
        )

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
    assert cross_account_update.status_code == 404
    changed = next(item for item in refreshed.json()["items"] if item["id"] == transaction["id"])
    assert changed["category_id"] == other["id"]
    assert all(item["category_id"] == other["id"] for item in refreshed.json()["items"])
    assert changed["tags"] == ["household", "reviewed"]
