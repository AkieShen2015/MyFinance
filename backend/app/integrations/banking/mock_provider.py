from datetime import date
from decimal import Decimal

from app.integrations.banking.base import (
    ProviderAccount,
    ProviderInstitution,
    ProviderTransaction,
    TransactionPage,
)
from app.models.enums import AccountType, TransactionType


def month_date(anchor: date, offset: int, day: int) -> date:
    month_index = anchor.year * 12 + anchor.month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, day)


class MockBankProvider:
    """Deterministic provider fixture; it never accepts real bank credentials."""

    name = "mock"
    page_size = 40

    def __init__(self, anchor: date = date(2026, 8, 15)) -> None:
        self.anchor = anchor
        self._institutions = (
            ProviderInstitution("mock-anz", "ANZ"),
            ProviderInstitution("mock-commbank", "Commonwealth Bank"),
        )
        self._accounts = (
            ProviderAccount(
                "anz-everyday",
                "mock-anz",
                "Everyday Account",
                AccountType.TRANSACTION,
                "•••• 1842",
                Decimal("4280.42"),
                Decimal("4280.42"),
            ),
            ProviderAccount(
                "anz-savings",
                "mock-anz",
                "Online Saver",
                AccountType.SAVINGS,
                "•••• 9017",
                Decimal("18750.00"),
                Decimal("18750.00"),
            ),
            ProviderAccount(
                "cba-credit",
                "mock-commbank",
                "Awards Credit Card",
                AccountType.CREDIT_CARD,
                "•••• 5521",
                Decimal("-1260.31"),
                Decimal("6739.69"),
            ),
        )
        self._transactions = self._build_transactions()

    async def get_institutions(self) -> tuple[ProviderInstitution, ...]:
        return self._institutions

    async def create_consent(self, user_reference: str) -> str:
        return f"mock-consent:{user_reference}"

    async def get_connections(self, user_reference: str) -> tuple[str, ...]:
        return (f"mock-connection:{user_reference}:anz", f"mock-connection:{user_reference}:cba")

    async def get_accounts(self, connection_id: str) -> tuple[ProviderAccount, ...]:
        institution_id = "mock-anz" if connection_id.endswith(":anz") else "mock-commbank"
        return tuple(a for a in self._accounts if a.institution_external_id == institution_id)

    async def get_transactions(
        self, account_external_id: str, cursor: str | None = None
    ) -> TransactionPage:
        account_transactions = tuple(
            tx for tx in self._transactions if tx.account_external_id == account_external_id
        )
        start = int(cursor or "0")
        end = start + self.page_size
        next_cursor = str(end) if end < len(account_transactions) else None
        return TransactionPage(account_transactions[start:end], next_cursor)

    async def refresh_connection(self, connection_id: str) -> None:
        if not connection_id.startswith("mock-connection:") or not connection_id.endswith(
            (":anz", ":cba")
        ):
            raise ValueError("Unknown mock connection")

    async def revoke_connection(self, connection_id: str) -> None:
        await self.refresh_connection(connection_id)

    def _build_transactions(self) -> tuple[ProviderTransaction, ...]:
        rows: list[ProviderTransaction] = []
        for month_offset in range(-11, 1):
            month_key = month_date(self.anchor, month_offset, 1).strftime("%Y%m")
            salary = Decimal("8420.00") + Decimal(20 * (month_offset + 11))
            rows.append(
                self._tx(
                    month_key,
                    "salary",
                    "anz-everyday",
                    1,
                    "ACME PTY LTD PAYROLL",
                    salary,
                    "Salary",
                )
            )
            rows.append(
                self._tx(
                    month_key,
                    "rent",
                    "anz-everyday",
                    2,
                    "RENT PAYMENT",
                    Decimal("-2100"),
                    "Rent",
                )
            )
            for week, amount in enumerate(("-138.42", "-151.08", "-129.65", "-164.22"), start=1):
                rows.append(
                    self._tx(
                        month_key,
                        f"woolworths-{week}",
                        "anz-everyday",
                        3 + week * 6,
                        f"WOOLWORTHS {1200 + week} SYDNEY",
                        Decimal(amount) - Decimal(month_offset + 11),
                        "Groceries",
                    )
                )
            rows.extend(
                (
                    self._tx(
                        month_key,
                        "netflix",
                        "cba-credit",
                        15,
                        "NETFLIX.COM",
                        Decimal("-25.99"),
                        "Subscriptions",
                    ),
                    self._tx(
                        month_key,
                        "spotify",
                        "cba-credit",
                        17,
                        "SPOTIFY AU",
                        Decimal("-13.99"),
                        "Subscriptions",
                    ),
                    self._tx(
                        month_key,
                        "icloud",
                        "cba-credit",
                        19,
                        "APPLE.COM/BILL ICLOUD",
                        Decimal("-4.49"),
                        "Subscriptions",
                    ),
                    self._tx(
                        month_key,
                        "gym",
                        "anz-everyday",
                        8,
                        "FITNESS FIRST",
                        Decimal("-59.00"),
                        "Fitness",
                    ),
                    self._tx(
                        month_key,
                        "electricity",
                        "anz-everyday",
                        12,
                        "ENERGY AUSTRALIA",
                        Decimal("-184.70"),
                        "Utilities",
                    ),
                    self._tx(
                        month_key,
                        "restaurant",
                        "cba-credit",
                        21,
                        "HARBOUR DINING",
                        Decimal("-142.30")
                        - Decimal(3 * (month_offset + 11)),
                        "Restaurants",
                    ),
                    self._tx(
                        month_key,
                        "opal",
                        "anz-everyday",
                        23,
                        "TRANSPORT NSW OPAL",
                        Decimal("-82.40"),
                        "Public Transport",
                    ),
                    self._tx(
                        month_key,
                        "fuel",
                        "cba-credit",
                        25,
                        "SHELL COLES EXPRESS",
                        Decimal("-76.20"),
                        "Fuel",
                    ),
                    self._tx(
                        month_key,
                        "interest",
                        "anz-savings",
                        28,
                        "INTEREST PAID",
                        Decimal("42.15"),
                        "Interest",
                    ),
                )
            )
            if month_offset % 3 == 0:
                rows.append(
                    self._tx(
                        month_key,
                        "petbarn",
                        "cba-credit",
                        10,
                        "PETBARN ALEXANDRIA",
                        Decimal("-186.40"),
                        "Pet Supplies",
                    )
                )
            if month_offset in (-8, -3):
                rows.append(
                    self._tx(
                        month_key,
                        "vet",
                        "cba-credit",
                        14,
                        "SYDNEY ANIMAL HOSPITAL",
                        Decimal("-685.00"),
                        "Veterinary",
                    )
                )
            if month_offset == -5:
                rows.append(
                    self._tx(
                        month_key,
                        "appliance",
                        "cba-credit",
                        20,
                        "THE GOOD GUYS",
                        Decimal("-1649.00"),
                        "Electronics",
                    )
                )
        return tuple(
            sorted(
                rows,
                key=lambda tx: (
                    tx.account_external_id,
                    tx.transaction_date,
                    tx.external_id,
                ),
            )
        )

    def _tx(
        self,
        month_key: str,
        key: str,
        account: str,
        day: int,
        description: str,
        amount: Decimal,
        category: str,
    ) -> ProviderTransaction:
        month_start = date(int(month_key[:4]), int(month_key[4:]), 1)
        transaction_date = month_start.replace(day=min(day, 28))
        transaction_type = TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE
        return ProviderTransaction(
            external_id=f"mock-{account}-{month_key}-{key}",
            account_external_id=account,
            transaction_date=transaction_date,
            posted_date=transaction_date,
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            provider_category=category,
        )
