from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies.current_user import CurrentUser, DatabaseSession
from app.models.enums import TransactionType
from app.repositories.finance_read import (
    get_overview,
    list_accounts,
    list_categories,
    list_transactions,
)
from app.schemas.finance import (
    AccountRead,
    CategoryRead,
    OverviewRead,
    TransactionCategoryUpdate,
    TransactionPage,
    TransactionTagsUpdate,
)
from app.services.transaction_updates import replace_tags, update_category

router = APIRouter(tags=["finance"])


@router.get("/overview", response_model=OverviewRead)
def overview(db: DatabaseSession, user: CurrentUser) -> OverviewRead:
    return get_overview(db, user.id)


@router.get("/accounts", response_model=list[AccountRead])
def accounts(db: DatabaseSession, user: CurrentUser) -> list[AccountRead]:
    return list_accounts(db, user.id)


@router.get("/categories", response_model=list[CategoryRead])
def categories(db: DatabaseSession, user: CurrentUser) -> list[CategoryRead]:
    return list_categories(db, user.id)


@router.get("/transactions", response_model=TransactionPage)
def transactions(
    db: DatabaseSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    account_id: UUID | None = None,
    institution_id: UUID | None = None,
    category_id: UUID | None = None,
    merchant_id: UUID | None = None,
    transaction_type: TransactionType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
) -> TransactionPage:
    return list_transactions(
        db,
        user.id,
        limit=limit,
        offset=offset,
        account_id=account_id,
        institution_id=institution_id,
        category_id=category_id,
        merchant_id=merchant_id,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        search=search,
    )


@router.patch("/transactions/{transaction_id}/category", status_code=status.HTTP_204_NO_CONTENT)
def transaction_category(
    transaction_id: UUID,
    payload: TransactionCategoryUpdate,
    db: DatabaseSession,
    user: CurrentUser,
) -> Response:
    update_category(
        db,
        user.id,
        transaction_id,
        payload.category_id,
        apply_to_similar=payload.apply_to_similar,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/transactions/{transaction_id}/tags", status_code=status.HTTP_204_NO_CONTENT)
def transaction_tags(
    transaction_id: UUID,
    payload: TransactionTagsUpdate,
    db: DatabaseSession,
    user: CurrentUser,
) -> Response:
    replace_tags(db, user.id, transaction_id, payload.tags)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
