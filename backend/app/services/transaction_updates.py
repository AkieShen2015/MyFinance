from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.enums import RuleMatchType
from app.models.finance import (
    Account,
    CategorisationRule,
    Category,
    Transaction,
    TransactionTag,
    transaction_tag_links,
)


def owned_transaction(db: Session, user_id: UUID, transaction_id: UUID) -> Transaction:
    transaction = db.scalar(
        select(Transaction)
        .join(Account)
        .where(Transaction.id == transaction_id, Account.user_id == user_id)
    )
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction


def update_category(
    db: Session,
    user_id: UUID,
    transaction_id: UUID,
    category_id: UUID,
    *,
    apply_to_similar: bool,
) -> None:
    transaction = owned_transaction(db, user_id, transaction_id)
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            (Category.is_system.is_(True))
            | (
                (Category.user_id == user_id)
                & (Category.account_id == transaction.account_id)
            ),
        )
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    transaction.category_id = category.id
    if apply_to_similar:
        match_type = (
            RuleMatchType.MERCHANT
            if transaction.merchant_id is not None
            else RuleMatchType.DESCRIPTION_EXACT
        )
        match_value = str(
            transaction.merchant_id
            or transaction.normalised_description
            or transaction.description
        )
        rule = db.scalar(
            select(CategorisationRule).where(
                CategorisationRule.user_id == user_id,
                CategorisationRule.match_type == match_type,
                CategorisationRule.match_value == match_value,
            )
        )
        if rule is None:
            rule = CategorisationRule(
                user_id=user_id,
                match_type=match_type,
                match_value=match_value,
                merchant_id=transaction.merchant_id,
                category_id=category.id,
                priority=10,
                enabled=True,
            )
            db.add(rule)
        else:
            rule.category_id = category.id
            rule.enabled = True
        similar_filters = [
            Account.user_id == user_id,
            Transaction.id != transaction.id,
            (
                Transaction.merchant_id == transaction.merchant_id
                if transaction.merchant_id is not None
                else Transaction.normalised_description
                == transaction.normalised_description
            ),
        ]
        if category.account_id is not None:
            similar_filters.append(Account.id == transaction.account_id)
        similar_transactions = db.scalars(
            select(Transaction)
            .join(Account)
            .where(*similar_filters)
        ).all()
        for similar_transaction in similar_transactions:
            similar_transaction.category_id = category.id
    db.commit()


def replace_tags(db: Session, user_id: UUID, transaction_id: UUID, names: list[str]) -> None:
    transaction = owned_transaction(db, user_id, transaction_id)
    cleaned = sorted({name.strip() for name in names if name.strip()}, key=str.casefold)
    if any(len(name) > 100 for name in cleaned):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tag is too long",
        )
    db.execute(
        delete(transaction_tag_links).where(
            transaction_tag_links.c.transaction_id == transaction.id
        )
    )
    for name in cleaned:
        tag = db.scalar(
            select(TransactionTag).where(
                TransactionTag.user_id == user_id, TransactionTag.name == name
            )
        )
        if tag is None:
            tag = TransactionTag(user_id=user_id, name=name)
            db.add(tag)
            db.flush()
        transaction.tags.append(tag)
    db.commit()
