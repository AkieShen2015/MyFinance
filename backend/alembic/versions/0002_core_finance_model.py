"""Create the core finance model.

Revision ID: 0002_core_finance_model
Revises: 0001_foundation
"""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa

from alembic import op

revision: str = "0002_core_finance_model"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column[Any]]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "institutions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("logo_url", sa.String(2048), nullable=True),
        sa.Column("country", sa.String(2), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_id", name="uq_institution_provider_external"),
    )

    op.create_table(
        "merchants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("canonical_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("merchant_type", sa.String(100), nullable=True),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_name"),
    )
    op.create_index("ix_merchants_canonical_name", "merchants", ["canonical_name"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("type", sa.String(8), nullable=False),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        *timestamps(),
        sa.CheckConstraint(
            "(is_system = true AND user_id IS NULL) OR (is_system = false AND user_id IS NOT NULL)",
            name="ck_category_system_owner",
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "parent_id", "name", name="uq_category_owner_parent_name"),
    )
    op.create_index("ix_categories_user_parent", "categories", ["user_id", "parent_id"])

    op.create_table(
        "bank_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_connection_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(7), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_expires_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider", "provider_connection_id", name="uq_connection_provider_external"
        ),
    )
    op.create_index(
        "ix_bank_connections_user_status", "bank_connections", ["user_id", "status"]
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("bank_connection_id", sa.Uuid(), nullable=False),
        sa.Column("institution_id", sa.Uuid(), nullable=False),
        sa.Column("external_account_id", sa.String(255), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(11), nullable=False),
        sa.Column("masked_account_number", sa.String(32), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("current_balance", sa.Numeric(19, 4), nullable=False),
        sa.Column("available_balance", sa.Numeric(19, 4), nullable=True),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["bank_connection_id"], ["bank_connections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "bank_connection_id", "external_account_id", name="uq_account_connection_external"
        ),
    )
    op.create_index("ix_accounts_user_institution", "accounts", ["user_id", "institution_id"])

    op.create_table(
        "transaction_tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_transaction_tag_user_name"),
    )

    op.create_table(
        "categorisation_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("match_type", sa.String(20), nullable=False),
        sa.Column("match_value", sa.String(500), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), nullable=True),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.CheckConstraint("priority >= 0", name="ck_categorisation_rule_priority_nonnegative"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_categorisation_rules_user_enabled_priority",
        "categorisation_rules",
        ["user_id", "enabled", "priority"],
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("external_transaction_id", sa.String(255), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("posted_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("normalised_description", sa.Text(), nullable=True),
        sa.Column("merchant_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("transaction_type", sa.String(8), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("pending", sa.Boolean(), nullable=False),
        sa.Column("provider_category", sa.String(255), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        *timestamps(),
        sa.CheckConstraint("amount <> 0", name="ck_transaction_amount_nonzero"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id", "external_transaction_id", name="uq_transaction_account_external"
        ),
    )
    op.create_index(
        "ix_transactions_account_date", "transactions", ["account_id", "transaction_date"]
    )
    op.create_index(
        "ix_transactions_category_date", "transactions", ["category_id", "transaction_date"]
    )
    op.create_index(
        "ix_transactions_merchant_date", "transactions", ["merchant_id", "transaction_date"]
    )

    op.create_table(
        "transaction_tag_links",
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["transaction_tags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("transaction_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("transaction_tag_links")
    op.drop_index("ix_transactions_merchant_date", table_name="transactions")
    op.drop_index("ix_transactions_category_date", table_name="transactions")
    op.drop_index("ix_transactions_account_date", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(
        "ix_categorisation_rules_user_enabled_priority", table_name="categorisation_rules"
    )
    op.drop_table("categorisation_rules")
    op.drop_table("transaction_tags")
    op.drop_index("ix_accounts_user_institution", table_name="accounts")
    op.drop_table("accounts")
    op.drop_index("ix_bank_connections_user_status", table_name="bank_connections")
    op.drop_table("bank_connections")
    op.drop_index("ix_categories_user_parent", table_name="categories")
    op.drop_table("categories")
    op.drop_index("ix_merchants_canonical_name", table_name="merchants")
    op.drop_table("merchants")
    op.drop_table("institutions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
