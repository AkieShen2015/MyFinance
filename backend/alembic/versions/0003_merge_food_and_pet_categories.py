"""Merge food and pet system categories.

Revision ID: 0003_merge_food_pet_categories
Revises: 0002_core_finance_model
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision: str = "0003_merge_food_pet_categories"
down_revision: str | None = "0002_core_finance_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


categories = sa.table(
    "categories",
    sa.column("id", sa.Uuid()),
    sa.column("name", sa.String()),
    sa.column("parent_id", sa.Uuid()),
    sa.column("type", sa.String()),
    sa.column("icon", sa.String()),
    sa.column("is_system", sa.Boolean()),
    sa.column("user_id", sa.Uuid()),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def _system_category_id(name: str, parent_id: Any = None) -> Any:
    connection = op.get_bind()
    statement = sa.select(categories.c.id).where(
        categories.c.name == name,
        categories.c.is_system.is_(True),
    )
    statement = statement.where(
        categories.c.parent_id.is_(None)
        if parent_id is None
        else categories.c.parent_id == parent_id
    )
    return connection.execute(statement).scalar_one_or_none()


def _reassign_category(source_ids: list[Any], target_id: Any) -> None:
    if not source_ids:
        return
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE transactions SET category_id = :target WHERE category_id IN :sources")
        .bindparams(sa.bindparam("sources", expanding=True)),
        {"target": target_id, "sources": source_ids},
    )
    connection.execute(
        sa.text(
            "UPDATE categorisation_rules SET category_id = :target "
            "WHERE category_id IN :sources"
        ).bindparams(sa.bindparam("sources", expanding=True)),
        {"target": target_id, "sources": source_ids},
    )


def upgrade() -> None:
    connection = op.get_bind()
    food_id = _system_category_id("Food")
    if food_id is not None:
        restaurant_id = _system_category_id("Restaurants", food_id)
        if restaurant_id is not None:
            _reassign_category([restaurant_id], food_id)
            connection.execute(
                sa.delete(categories).where(categories.c.id == restaurant_id)
            )
        connection.execute(
            sa.update(categories)
            .where(categories.c.parent_id == food_id)
            .values(parent_id=None)
        )
        connection.execute(
            sa.update(categories)
            .where(categories.c.id == food_id)
            .values(name="Food & Restaurant")
        )

    pet_id = _system_category_id("Pet")
    if pet_id is not None:
        pet_child_ids = list(
            connection.execute(
                sa.select(categories.c.id).where(categories.c.parent_id == pet_id)
            ).scalars()
        )
        _reassign_category(pet_child_ids, pet_id)
        if pet_child_ids:
            connection.execute(
                sa.delete(categories).where(categories.c.id.in_(pet_child_ids))
            )


def downgrade() -> None:
    connection = op.get_bind()
    now = datetime.now(UTC)
    food_id = _system_category_id("Food & Restaurant")
    if food_id is not None:
        connection.execute(
            sa.update(categories).where(categories.c.id == food_id).values(name="Food")
        )
        connection.execute(
            sa.insert(categories).values(
                id=uuid4(),
                name="Restaurants",
                parent_id=food_id,
                type="expense",
                icon=None,
                is_system=True,
                user_id=None,
                created_at=now,
                updated_at=now,
            )
        )

    pet_id = _system_category_id("Pet")
    if pet_id is not None:
        connection.execute(
            sa.insert(categories),
            [
                {
                    "id": uuid4(),
                    "name": name,
                    "parent_id": pet_id,
                    "type": "expense",
                    "icon": None,
                    "is_system": True,
                    "user_id": None,
                    "created_at": now,
                    "updated_at": now,
                }
                for name in ("Vet", "Food", "Medication", "Insurance", "Supplies")
            ],
        )
