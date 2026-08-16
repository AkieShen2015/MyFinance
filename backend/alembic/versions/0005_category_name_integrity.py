"""Strengthen account category name uniqueness.

Revision ID: 0005_category_name_integrity
Revises: 0004_account_scoped_categories
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_category_name_integrity"
down_revision: str | None = "0004_account_scoped_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_category_owner_account_parent_name", "categories", type_="unique"
    )
    op.create_unique_constraint(
        "uq_category_owner_account_parent_name",
        "categories",
        ["user_id", "account_id", "parent_id", "name"],
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_category_owner_account_parent_name", "categories", type_="unique"
    )
    op.create_unique_constraint(
        "uq_category_owner_account_parent_name",
        "categories",
        ["user_id", "account_id", "parent_id", "name"],
    )
