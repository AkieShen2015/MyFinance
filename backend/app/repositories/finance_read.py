from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

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
            type=item.type,
            icon=item.icon,
            is_system=item.is_system,
        )
        for item in categories
    ]


def list_transactions(
    db: Session, user_id: UUID, *, limit: int, offset: int
) -> TransactionPage:
    owner_filter = Account.user_id == user_id
    total = db.scalar(
        select(func.count(Transaction.id)).join(Account).where(owner_filter)
    ) or 0
    rows = db.execute(
        select(Transaction, Account, Institution, Merchant, Category)
        .join(Account, Account.id == Transaction.account_id)
        .join(Institution, Institution.id == Account.institution_id)
        .outerjoin(Merchant, Merchant.id == Transaction.merchant_id)
        .outerjoin(Category, Category.id == Transaction.category_id)
        .options(selectinload(Transaction.tags))
        .where(owner_filter)
        .order_by(Transaction.transaction_date.desc(), Transaction.id)
        .limit(limit)
        .offset(offset)
    ).all()
    items = [
        TransactionRead(
            id=transaction.id,
            transaction_date=transaction.transaction_date,
            institution_name=institution.name,
            account_name=account.account_name,
            merchant_name=merchant.display_name if merchant else None,
            description=transaction.description,
            category_name=category.name if category else None,
            tags=[tag.name for tag in transaction.tags],
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            currency=transaction.currency,
            pending=transaction.pending,
        )
        for transaction, account, institution, merchant, category in rows
    ]
    return TransactionPage(items=items, total=total, limit=limit, offset=offset)


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

