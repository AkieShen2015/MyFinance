from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

from app.models.enums import AccountType, TransactionStatus, TransactionType


@dataclass(frozen=True)
class ProviderInstitution:
    external_id: str
    name: str
    logo_url: str | None = None
    country: str = "AU"


@dataclass(frozen=True)
class ProviderAccount:
    external_id: str
    institution_external_id: str
    name: str
    account_type: AccountType
    masked_account_number: str
    current_balance: Decimal
    available_balance: Decimal | None
    currency: str = "AUD"


@dataclass(frozen=True)
class ProviderTransaction:
    external_id: str
    account_external_id: str
    transaction_date: date
    posted_date: date | None
    description: str
    amount: Decimal
    transaction_type: TransactionType
    provider_category: str | None
    status: TransactionStatus = TransactionStatus.POSTED
    currency: str = "AUD"


@dataclass(frozen=True)
class TransactionPage:
    transactions: tuple[ProviderTransaction, ...]
    next_cursor: str | None


class BankProvider(Protocol):
    name: str

    async def get_institutions(self) -> tuple[ProviderInstitution, ...]: ...

    async def create_consent(self, user_reference: str) -> str: ...

    async def get_connections(self, user_reference: str) -> tuple[str, ...]: ...

    async def get_accounts(self, connection_id: str) -> tuple[ProviderAccount, ...]: ...

    async def get_transactions(
        self, account_external_id: str, cursor: str | None = None
    ) -> TransactionPage: ...

    async def refresh_connection(self, connection_id: str) -> None: ...

    async def revoke_connection(self, connection_id: str) -> None: ...

