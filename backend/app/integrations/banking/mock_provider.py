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
            ProviderInstitution("mock-nab", "NAB"),
            ProviderInstitution("mock-westpac", "Westpac"),
            ProviderInstitution("mock-ing", "ING"),
            ProviderInstitution("mock-hsbc", "HSBC"),
            ProviderInstitution("mock-bankwest", "Bankwest"),
            ProviderInstitution("mock-st-george", "St.George"),
            ProviderInstitution("mock-latitude", "Latitude"),
            ProviderInstitution("mock-macquarie", "Macquarie Bank"),
            ProviderInstitution("mock-suncorp", "Suncorp Bank"),
            ProviderInstitution("mock-bendigo", "Bendigo Bank"),
            ProviderInstitution("mock-boq", "Bank of Queensland"),
            ProviderInstitution("mock-ubank", "ubank"),
        )
        self._accounts: tuple[ProviderAccount, ...] = (
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
        additional_accounts: tuple[
            tuple[str, str, str, AccountType, str, str, str], ...
        ] = (
            (
                "anz-business",
                "mock-nab",
                "NAB Reward Saver",
                AccountType.TRANSACTION,
                "•••• 7643",
                "9250.80",
                "9250.80",
            ),
            (
                "anz-progress-saver",
                "mock-westpac",
                "Westpac Choice",
                AccountType.SAVINGS,
                "•••• 2208",
                "6350.25",
                "6350.25",
            ),
            (
                "anz-travel",
                "mock-ing",
                "Orange Everyday",
                AccountType.TRANSACTION,
                "•••• 3374",
                "2180.40",
                "2180.40",
            ),
            (
                "anz-offset",
                "mock-hsbc",
                "Everyday Global Account",
                AccountType.TRANSACTION,
                "•••• 6159",
                "32400.00",
                "32400.00",
            ),
            (
                "anz-investing-cash",
                "mock-bankwest",
                "Easy Transaction Account",
                AccountType.TRANSACTION,
                "•••• 4826",
                "5780.15",
                "5780.15",
            ),
            (
                "anz-online-business-saver",
                "mock-st-george",
                "Complete Freedom",
                AccountType.TRANSACTION,
                "•••• 1085",
                "14820.60",
                "14820.60",
            ),
            (
                "cba-smart-access",
                "mock-latitude",
                "28° Global Platinum",
                AccountType.CREDIT_CARD,
                "•••• 4920",
                "3460.18",
                "3460.18",
            ),
            (
                "cba-netbank-saver",
                "mock-macquarie",
                "Transaction Account",
                AccountType.TRANSACTION,
                "•••• 7314",
                "11250.75",
                "11250.75",
            ),
            (
                "cba-goalsaver",
                "mock-suncorp",
                "Growth Saver",
                AccountType.SAVINGS,
                "•••• 8453",
                "8040.20",
                "8040.20",
            ),
            (
                "cba-complete-access",
                "mock-bendigo",
                "Easy Money",
                AccountType.TRANSACTION,
                "•••• 2697",
                "1965.32",
                "1965.32",
            ),
            (
                "cba-low-fee-card",
                "mock-boq",
                "Future Saver",
                AccountType.SAVINGS,
                "•••• 9136",
                "-480.64",
                "3519.36",
            ),
            (
                "cba-business-transaction",
                "mock-ubank",
                "Spend Account",
                AccountType.TRANSACTION,
                "•••• 6041",
                "12640.90",
                "12640.90",
            ),
        )
        self._accounts += tuple(
            ProviderAccount(
                external_id,
                institution_id,
                name,
                account_type,
                masked_number,
                Decimal(current_balance),
                Decimal(available_balance),
            )
            for (
                external_id,
                institution_id,
                name,
                account_type,
                masked_number,
                current_balance,
                available_balance,
            ) in additional_accounts
        )
        self._transactions = self._build_transactions()

    async def get_institutions(self) -> tuple[ProviderInstitution, ...]:
        return self._institutions

    async def create_consent(self, user_reference: str) -> str:
        return f"mock-consent:{user_reference}"

    async def get_connections(self, user_reference: str) -> tuple[str, ...]:
        return tuple(
            f"mock-connection:{user_reference}:{institution.external_id.removeprefix('mock-')}"
            for institution in self._institutions
        )

    async def get_accounts(self, connection_id: str) -> tuple[ProviderAccount, ...]:
        institution_id = f"mock-{connection_id.rsplit(':', maxsplit=1)[-1]}"
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
        institution_id = f"mock-{connection_id.rsplit(':', maxsplit=1)[-1]}"
        institution_ids = {institution.external_id for institution in self._institutions}
        if (
            not connection_id.startswith("mock-connection:")
            or institution_id not in institution_ids
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
        current_month = self.anchor.strftime("%Y%m")
        rows.extend(
            (
                self._tx(
                    current_month,
                    "canberra-cat-vet",
                    "anz-everyday",
                    5,
                    "CANBERRA CAT VET BELCONNEN 035",
                    Decimal("-386.00"),
                    "Veterinary",
                ),
                self._tx(
                    current_month,
                    "zlbel",
                    "anz-everyday",
                    7,
                    "ZLBEL PTY LTD WESTON",
                    Decimal("-19.53"),
                    None,
                ),
                self._tx(
                    current_month,
                    "kwafood",
                    "cba-credit",
                    9,
                    "SQ *KWAFOOD 1982 CANBERRA",
                    Decimal("-22.79"),
                    "Restaurants",
                ),
                self._tx(
                    current_month,
                    "yijia-grocery",
                    "anz-everyday",
                    11,
                    "YIJIA ASIAN GROCERY",
                    Decimal("-55.29"),
                    "Groceries",
                ),
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
        category: str | None,
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
