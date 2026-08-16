import asyncio
from datetime import date

from app.integrations.banking.mock_provider import MockBankProvider


def test_mock_provider_exposes_fifteen_accounts_across_institutions() -> None:
    provider = MockBankProvider()

    async def collect_accounts() -> tuple[int, int]:
        institutions = await provider.get_institutions()
        connections = await provider.get_connections("demo-user")
        accounts = [
            account
            for connection in connections
            for account in await provider.get_accounts(connection)
        ]
        return len(institutions), len(accounts)

    assert asyncio.run(collect_accounts()) == (14, 15)


def test_mock_provider_has_rich_twelve_month_history() -> None:
    provider = MockBankProvider(anchor=date(2026, 8, 15))

    async def collect() -> list[object]:
        transactions: list[object] = []
        cursor: str | None = None
        while True:
            page = await provider.get_transactions("anz-everyday", cursor)
            transactions.extend(page.transactions)
            if page.next_cursor is None:
                return transactions
            cursor = page.next_cursor

    transactions = asyncio.run(collect())
    dates = [transaction.transaction_date for transaction in transactions]  # type: ignore[attr-defined]
    descriptions = [transaction.description for transaction in transactions]  # type: ignore[attr-defined]

    assert len({(item.year, item.month) for item in dates}) == 12
    assert len(transactions) > provider.page_size
    assert sum("NETFLIX" in item for item in descriptions) == 0
    assert sum("WOOLWORTHS" in item for item in descriptions) == 48


def test_mock_credit_card_contains_recurring_and_irregular_expenses() -> None:
    provider = MockBankProvider()

    async def collect() -> list[object]:
        transactions: list[object] = []
        cursor: str | None = None
        while True:
            page = await provider.get_transactions("cba-credit", cursor)
            transactions.extend(page.transactions)
            if page.next_cursor is None:
                return transactions
            cursor = page.next_cursor

    transactions = asyncio.run(collect())
    descriptions = [transaction.description for transaction in transactions]  # type: ignore[attr-defined]

    assert sum("NETFLIX" in item for item in descriptions) == 12
    assert any("GOOD GUYS" in item for item in descriptions)
    assert any("ANIMAL HOSPITAL" in item for item in descriptions)
