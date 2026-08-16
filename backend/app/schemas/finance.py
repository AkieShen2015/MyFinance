from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountType, CategoryType, ConnectionStatus, TransactionType


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_name: str
    account_name: str
    account_type: AccountType
    masked_account_number: str | None
    currency: str
    current_balance: Decimal
    available_balance: Decimal | None
    connection_status: ConnectionStatus
    last_sync_at: datetime | None


class CategoryRead(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None
    type: CategoryType
    icon: str | None
    is_system: bool


class TransactionRead(BaseModel):
    id: UUID
    transaction_date: date
    institution_name: str
    account_name: str
    merchant_name: str | None
    description: str
    category_name: str | None
    tags: list[str]
    transaction_type: TransactionType
    amount: Decimal
    currency: str
    pending: bool


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


class OverviewRead(BaseModel):
    account_count: int = Field(ge=0)
    transaction_count: int = Field(ge=0)
    category_count: int = Field(ge=0)
    total_balance: Decimal
    currency: str = "AUD"

