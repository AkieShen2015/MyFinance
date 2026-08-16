from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import TransactionType
from app.models.finance import (
    Account,
    BankConnection,
    Category,
    Institution,
    Merchant,
    Transaction,
)
from app.schemas.finance import (
    AccountRead,
    CategoryRead,
    OverviewRead,
    TransactionPage,
    TransactionRead,
)


def list_accounts(db: Session, user_id: UUID) -> list[AccountRead]:
    rows = db.execute(
        select(Account, Institution, BankConnection)
        .join(Institution, Institution.id == Account.institution_id)
        .join(BankConnection, BankConnection.id == Account.bank_connection_id)
        .where(Account.user_id == user_id)
        .order_by(Institution.name, Account.account_name)
    ).all()
    return [
        AccountRead(
            id=account.id,
            institution_id=institution.id,
            institution_name=institution.name,
            account_name=account.account_name,
            account_type=account.account_type,
            masked_account_number=account.masked_account_number,
            currency=account.currency,
            current_balance=account.current_balance,
            available_balance=account.available_balance,
            connection_status=connection.status,
            last_sync_at=connection.last_sync_at,
        )
        for account, institution, connection in rows
    ]


def list_categories(db: Session, user_id: UUID) -> list[CategoryRead]:
    categories = db.scalars(
        select(Category)
        .where((Category.user_id.is_(None)) | (Category.user_id == user_id))
        .order_by(Category.type, Category.parent_id, Category.name)
    ).all()
    return [
        CategoryRead(
            id=item.id,
            name=item.name,
            parent_id=item.parent_id,
            account_id=item.account_id,
            type=item.type,
            icon=item.icon,
            is_system=item.is_system,
        )
        for item in categories
    ]


def list_transactions(
    db: Session,
    user_id: UUID,
    *,
    limit: int,
    offset: int,
    account_id: UUID | None = None,
    institution_id: UUID | None = None,
    category_id: UUID | None = None,
    merchant_id: UUID | None = None,
    transaction_type: TransactionType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
    search: str | None = None,
    sort_by: Literal["transaction_date", "amount", "merchant"] = "transaction_date",
    sort_order: Literal["asc", "desc"] = "desc",
) -> TransactionPage:
    filters = [Account.user_id == user_id]
    if account_id:
        filters.append(Account.id == account_id)
    if institution_id:
        filters.append(Account.institution_id == institution_id)
    if category_id:
        filters.append(Transaction.category_id == category_id)
    if merchant_id:
        filters.append(Transaction.merchant_id == merchant_id)
    if transaction_type:
        filters.append(Transaction.transaction_type == transaction_type)
    if date_from:
        filters.append(Transaction.transaction_date >= date_from)
    if date_to:
        filters.append(Transaction.transaction_date <= date_to)
    if amount_min is not None:
        filters.append(Transaction.amount >= amount_min)
    if amount_max is not None:
        filters.append(Transaction.amount <= amount_max)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                Transaction.description.ilike(pattern),
                Transaction.normalised_description.ilike(pattern),
                Merchant.display_name.ilike(pattern),
            )
        )
    total = db.scalar(
        select(func.count(Transaction.id))
        .join(Account)
        .outerjoin(Merchant, Merchant.id == Transaction.merchant_id)
        .where(*filters)
    ) or 0
    sort_column = {
        "transaction_date": Transaction.transaction_date,
        "amount": Transaction.amount,
        "merchant": func.coalesce(Merchant.display_name, Transaction.description),
    }[sort_by]
    order_expression = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    rows = db.execute(
        select(Transaction, Account, Institution, Merchant, Category)
        .join(Account, Account.id == Transaction.account_id)
        .join(Institution, Institution.id == Account.institution_id)
        .outerjoin(Merchant, Merchant.id == Transaction.merchant_id)
        .outerjoin(Category, Category.id == Transaction.category_id)
        .options(selectinload(Transaction.tags))
        .where(*filters)
        .order_by(order_expression, Transaction.id)
        .limit(limit)
        .offset(offset)
    ).all()
    items = [
        TransactionRead(
            id=transaction.id,
            account_id=account.id,
            category_id=transaction.category_id,
            merchant_id=transaction.merchant_id,
            transaction_date=transaction.transaction_date,
            institution_name=institution.name,
            account_name=account.account_name,
            merchant_name=merchant.display_name if merchant else None,
            description=transaction.description,
            category_name=category.name if category else None,
            tags=sorted((tag.name for tag in transaction.tags), key=str.casefold),
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            currency=transaction.currency,
            pending=transaction.pending,
        )
        for transaction, account, institution, merchant, category in rows
    ]
    return TransactionPage(items=items, total=total, limit=limit, offset=offset)


def get_transaction(db: Session, user_id: UUID, transaction_id: UUID) -> TransactionRead | None:
    row = db.execute(
        select(Transaction, Account, Institution, Merchant, Category)
        .join(Account, Account.id == Transaction.account_id)
        .join(Institution, Institution.id == Account.institution_id)
        .outerjoin(Merchant, Merchant.id == Transaction.merchant_id)
        .outerjoin(Category, Category.id == Transaction.category_id)
        .options(selectinload(Transaction.tags))
        .where(Transaction.id == transaction_id, Account.user_id == user_id)
    ).one_or_none()
    if row is None:
        return None
    transaction, account, institution, merchant, category = row
    return TransactionRead(
        id=transaction.id,
        account_id=account.id,
        category_id=transaction.category_id,
        merchant_id=transaction.merchant_id,
        transaction_date=transaction.transaction_date,
        institution_name=institution.name,
        account_name=account.account_name,
        merchant_name=merchant.display_name if merchant else None,
        description=transaction.description,
        category_name=category.name if category else None,
        tags=sorted((tag.name for tag in transaction.tags), key=str.casefold),
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        currency=transaction.currency,
        pending=transaction.pending,
    )


def get_overview(db: Session, user_id: UUID) -> OverviewRead:
    account_count, total_balance = db.execute(
        select(func.count(Account.id), func.coalesce(func.sum(Account.current_balance), 0)).where(
            Account.user_id == user_id
        )
    ).one()
    transaction_count = db.scalar(
        select(func.count(Transaction.id)).join(Account).where(Account.user_id == user_id)
    ) or 0
    category_count = db.scalar(
        select(func.count(Category.id)).where(
            (Category.user_id.is_(None)) | (Category.user_id == user_id)
        )
    ) or 0
    return OverviewRead(
        account_count=account_count,
        transaction_count=transaction_count,
        category_count=category_count,
        total_balance=Decimal(total_balance),
    )
