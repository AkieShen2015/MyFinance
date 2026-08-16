import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import CategoryType
from app.models.finance import Account, Category

CATEGORY_ALIASES = {
    "food": "Food & Restaurant",
    "restaurant": "Food & Restaurant",
    "restaurants": "Food & Restaurant",
    "dining": "Food & Restaurant",
    "vet": "Pet",
    "veterinary": "Pet",
}


def _normalise_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()


def create_or_match_category(
    db: Session,
    user_id: UUID,
    account_id: UUID,
    name: str,
    category_type: CategoryType,
) -> Category:
    account_exists = db.scalar(
        select(Account.id).where(Account.id == account_id, Account.user_id == user_id)
    )
    if account_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    clean_name = " ".join(name.split())
    normalised_name = _normalise_name(clean_name)
    alias_name = CATEGORY_ALIASES.get(normalised_name)
    if alias_name is not None:
        matched = db.scalar(
            select(Category).where(
                Category.is_system.is_(True),
                func.lower(Category.name) == alias_name.casefold(),
            )
        )
        if matched is not None:
            return matched

    existing = db.scalar(
        select(Category).where(
            func.lower(Category.name) == clean_name.casefold(),
            (Category.is_system.is_(True))
            | ((Category.user_id == user_id) & (Category.account_id == account_id)),
        )
    )
    if existing is not None:
        return existing

    category = Category(
        account_id=account_id,
        is_system=False,
        name=clean_name,
        parent_id=None,
        type=category_type,
        user_id=user_id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
