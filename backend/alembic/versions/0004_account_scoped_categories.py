"""Add account-scoped custom categories.

Revision ID: 0004_account_scoped_categories
Revises: 0003_merge_food_pet_categories
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_account_scoped_categories"
down_revision: str | None = "0003_merge_food_pet_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("account_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_categories_account_id_accounts",
        "categories",
        "accounts",
        ["account_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("uq_category_owner_parent_name", "categories", type_="unique")
    op.drop_constraint("ck_category_system_owner", "categories", type_="check")
    op.create_unique_constraint(
        "uq_category_owner_account_parent_name",
        "categories",
        ["user_id", "account_id", "parent_id", "name"],
    )
    op.create_check_constraint(
        "ck_category_system_owner",
        "categories",
        "(is_system = true AND user_id IS NULL AND account_id IS NULL) OR "
        "(is_system = false AND user_id IS NOT NULL AND account_id IS NOT NULL)",
    )
    op.create_index("ix_categories_account_name", "categories", ["account_id", "name"])


def downgrade() -> None:
    op.drop_index("ix_categories_account_name", table_name="categories")
    op.drop_constraint("ck_category_system_owner", "categories", type_="check")
    op.drop_constraint(
        "uq_category_owner_account_parent_name", "categories", type_="unique"
    )
    op.create_unique_constraint(
        "uq_category_owner_parent_name",
        "categories",
        ["user_id", "parent_id", "name"],
    )
    op.create_check_constraint(
        "ck_category_system_owner",
        "categories",
        "(is_system = true AND user_id IS NULL) OR "
        "(is_system = false AND user_id IS NOT NULL)",
    )
    op.drop_constraint(
        "fk_categories_account_id_accounts", "categories", type_="foreignkey"
    )
    op.drop_column("categories", "account_id")
