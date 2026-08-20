from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountType, CategoryType, ConnectionStatus, TransactionType


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
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
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    parent_id: UUID | None
    account_id: UUID | None
    type: CategoryType
    icon: str | None
    is_system: bool


class TransactionRead(BaseModel):
    id: UUID
    account_id: UUID
    category_id: UUID | None
    merchant_id: UUID | None
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


class DashboardSummaryRead(BaseModel):
    date_from: date
    date_to: date
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    total_account_balance: Decimal
    currency: str = "AUD"


class ExpenseCategoryRead(BaseModel):
    category: str
    amount: Decimal = Field(ge=0)
    percentage: Decimal = Field(ge=0, le=100)


class IncomeExpenseMonthRead(BaseModel):
    month: date
    income: Decimal = Field(ge=0)
    expenses: Decimal = Field(ge=0)


class AnalyticsComparisonRead(BaseModel):
    current: Decimal
    previous: Decimal
    change_amount: Decimal
    change_percentage: Decimal | None


class MerchantSpendRead(BaseModel):
    merchant: str
    amount: Decimal = Field(ge=0)
    percentage: Decimal = Field(ge=0, le=100)
    transaction_count: int = Field(ge=1)


class RecurringPaymentRead(BaseModel):
    merchant: str
    average_amount: Decimal = Field(ge=0)
    occurrences: int = Field(ge=2)
    cadence_days: int = Field(ge=1)
    next_expected_date: date
    confidence: Decimal = Field(ge=0, le=1)


class SpendingAnomalyRead(BaseModel):
    transaction_id: UUID
    date: date
    merchant: str
    category: str
    amount: Decimal = Field(ge=0)
    baseline_amount: Decimal = Field(ge=0)
    multiple: Decimal = Field(ge=1)


class CategoryTrendPointRead(BaseModel):
    month: date
    amount: Decimal = Field(ge=0)


class CategoryTrendRead(BaseModel):
    category: str
    current_amount: Decimal = Field(ge=0)
    previous_amount: Decimal = Field(ge=0)
    change_amount: Decimal
    change_percentage: Decimal | None
    monthly: list[CategoryTrendPointRead]


class FinancialInsightRead(BaseModel):
    kind: str
    title: str
    message: str
    impact_amount: Decimal = Field(ge=0)
    confidence: Decimal = Field(ge=0, le=1)


class AiInsightPayloadRead(BaseModel):
    period_start: date
    period_end: date
    expense_change_amount: Decimal
    expense_change_percentage: Decimal | None
    top_category_changes: list[dict[str, str]]
    recurring_total: Decimal = Field(ge=0)
    anomaly_count: int = Field(ge=0)


class AnalyticsReportRead(BaseModel):
    date_from: date
    date_to: date
    previous_date_from: date
    previous_date_to: date
    income: AnalyticsComparisonRead
    expenses: AnalyticsComparisonRead
    net_cash_flow: AnalyticsComparisonRead
    savings_rate: Decimal | None
    category_trends: list[CategoryTrendRead]
    top_merchants: list[MerchantSpendRead]
    recurring_payments: list[RecurringPaymentRead]
    anomalies: list[SpendingAnomalyRead]
    insights: list[FinancialInsightRead]
    ai_payload: AiInsightPayloadRead


class TransactionCategoryUpdate(BaseModel):
    category_id: UUID
    apply_to_similar: bool = False


class CategoryCreate(BaseModel):
    account_id: UUID
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType


class TransactionTagsUpdate(BaseModel):
    tags: list[str] = Field(max_length=20)
