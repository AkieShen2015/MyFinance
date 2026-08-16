from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    AccountType,
    CategoryType,
    ConnectionStatus,
    RuleMatchType,
    TransactionStatus,
    TransactionType,
)


def enum_column(enum_type: type[Any], name: str) -> Enum:
    return Enum(
        enum_type,
        name=name,
        native_enum=False,
        values_callable=lambda items: [x.value for x in items],
    )


transaction_tag_links = Table(
    "transaction_tag_links",
    Base.metadata,
    Column(
        "transaction_id",
        ForeignKey("transactions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("tag_id", ForeignKey("transaction_tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)


class Institution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "institutions"
    __table_args__ = (
        UniqueConstraint(
            "provider", "external_id", name="uq_institution_provider_external"
        ),
    )

    provider: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    logo_url: Mapped[str | None] = mapped_column(String(2048))
    country: Mapped[str] = mapped_column(String(2), default="AU")


class BankConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "bank_connections"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_connection_id",
            name="uq_connection_provider_external",
        ),
        Index("ix_bank_connections_user_status", "user_id", "status"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    institution_id: Mapped[UUID] = mapped_column(ForeignKey("institutions.id", ondelete="RESTRICT"))
    provider: Mapped[str] = mapped_column(String(50))
    provider_connection_id: Mapped[str] = mapped_column(String(255))
    status: Mapped[ConnectionStatus] = mapped_column(
        enum_column(ConnectionStatus, "connection_status"),
        default=ConnectionStatus.PENDING,
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    institution: Mapped[Institution] = relationship()


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint(
            "bank_connection_id",
            "external_account_id",
            name="uq_account_connection_external",
        ),
        Index("ix_accounts_user_institution", "user_id", "institution_id"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    bank_connection_id: Mapped[UUID] = mapped_column(
        ForeignKey("bank_connections.id", ondelete="CASCADE")
    )
    institution_id: Mapped[UUID] = mapped_column(
        ForeignKey("institutions.id", ondelete="RESTRICT")
    )
    external_account_id: Mapped[str] = mapped_column(String(255))
    account_name: Mapped[str] = mapped_column(String(255))
    account_type: Mapped[AccountType] = mapped_column(enum_column(AccountType, "account_type"))
    masked_account_number: Mapped[str | None] = mapped_column(String(32))
    currency: Mapped[str] = mapped_column(String(3), default="AUD")
    current_balance: Mapped[Decimal] = mapped_column(Numeric(19, 4), default=Decimal("0"))
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))

    institution: Mapped[Institution] = relationship()
    bank_connection: Mapped[BankConnection] = relationship()


class Merchant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "merchants"

    canonical_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    merchant_type: Mapped[str | None] = mapped_column(String(100))


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "parent_id", "name", name="uq_category_owner_parent_name"
        ),
        CheckConstraint(
            "(is_system = true AND user_id IS NULL) OR (is_system = false AND user_id IS NOT NULL)",
            name="ck_category_system_owner",
        ),
        Index("ix_categories_user_parent", "user_id", "parent_id"),
    )

    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT")
    )
    type: Mapped[CategoryType] = mapped_column(enum_column(CategoryType, "category_type"))
    icon: Mapped[str | None] = mapped_column(String(100))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(back_populates="parent")


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "external_transaction_id",
            name="uq_transaction_account_external",
        ),
        Index("ix_transactions_account_date", "account_id", "transaction_date"),
        Index("ix_transactions_category_date", "category_id", "transaction_date"),
        Index("ix_transactions_merchant_date", "merchant_id", "transaction_date"),
        CheckConstraint("amount <> 0", name="ck_transaction_amount_nonzero"),
    )

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    external_transaction_id: Mapped[str] = mapped_column(String(255))
    transaction_date: Mapped[date] = mapped_column(Date)
    posted_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text)
    normalised_description: Mapped[str | None] = mapped_column(Text)
    merchant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="SET NULL")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4))
    currency: Mapped[str] = mapped_column(String(3), default="AUD")
    transaction_type: Mapped[TransactionType] = mapped_column(
        enum_column(TransactionType, "transaction_type")
    )
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL")
    )
    status: Mapped[TransactionStatus] = mapped_column(
        enum_column(TransactionStatus, "transaction_status"),
        default=TransactionStatus.POSTED,
    )
    pending: Mapped[bool] = mapped_column(Boolean, default=False)
    provider_category: Mapped[str | None] = mapped_column(String(255))
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    account: Mapped[Account] = relationship()
    merchant: Mapped[Merchant | None] = relationship()
    category: Mapped[Category | None] = relationship()
    tags: Mapped[list["TransactionTag"]] = relationship(
        secondary=transaction_tag_links, back_populates="transactions"
    )


class TransactionTag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transaction_tags"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_transaction_tag_user_name"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))

    transactions: Mapped[list[Transaction]] = relationship(
        secondary=transaction_tag_links, back_populates="tags"
    )


class CategorisationRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "categorisation_rules"
    __table_args__ = (
        Index(
            "ix_categorisation_rules_user_enabled_priority",
            "user_id",
            "enabled",
            "priority",
        ),
        CheckConstraint("priority >= 0", name="ck_categorisation_rule_priority_nonnegative"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    match_type: Mapped[RuleMatchType] = mapped_column(
        enum_column(RuleMatchType, "rule_match_type")
    )
    match_value: Mapped[str] = mapped_column(String(500))
    merchant_id: Mapped[UUID | None] = mapped_column(ForeignKey("merchants.id", ondelete="CASCADE"))
    category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    priority: Mapped[int] = mapped_column(Integer, default=100)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
