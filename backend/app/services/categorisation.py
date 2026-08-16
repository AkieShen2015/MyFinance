from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import RuleMatchType
from app.models.finance import CategorisationRule, Category


def category_id_from_saved_rules(
    session: Session,
    user_id: UUID,
    *,
    account_id: UUID,
    merchant_id: UUID | None,
    normalised_description: str,
    provider_category: str | None = None,
) -> UUID | None:
    """Return the highest-priority user rule that deterministically matches."""
    rules = session.scalars(
        select(CategorisationRule)
        .join(Category, Category.id == CategorisationRule.category_id)
        .where(
            CategorisationRule.user_id == user_id,
            CategorisationRule.enabled.is_(True),
            (Category.is_system.is_(True)) | (Category.account_id == account_id),
        )
        .order_by(CategorisationRule.priority, CategorisationRule.created_at)
    ).all()
    for rule in rules:
        if (
            rule.match_type == RuleMatchType.MERCHANT
            and merchant_id is not None
            and rule.merchant_id == merchant_id
        ):
            return rule.category_id
        if (
            rule.match_type == RuleMatchType.DESCRIPTION_EXACT
            and rule.match_value == normalised_description
        ):
            return rule.category_id
        if (
            rule.match_type == RuleMatchType.DESCRIPTION_CONTAINS
            and rule.match_value in normalised_description
        ):
            return rule.category_id
        if (
            rule.match_type == RuleMatchType.PROVIDER_CATEGORY
            and provider_category is not None
            and rule.match_value.casefold() == provider_category.casefold()
        ):
            return rule.category_id
    return None
