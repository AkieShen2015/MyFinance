from enum import StrEnum


class AccountType(StrEnum):
    TRANSACTION = "transaction"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    OTHER = "other"


class CategoryType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class ConnectionStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class RuleMatchType(StrEnum):
    MERCHANT = "merchant"
    DESCRIPTION_CONTAINS = "description_contains"
    DESCRIPTION_EXACT = "description_exact"
    PROVIDER_CATEGORY = "provider_category"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    POSTED = "posted"
    REVERSED = "reversed"


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"

