from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies.current_user import CurrentUser, DatabaseSession
from app.repositories.finance_read import (
    get_overview,
    list_accounts,
    list_categories,
    list_transactions,
)
from app.schemas.finance import AccountRead, CategoryRead, OverviewRead, TransactionPage

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
) -> TransactionPage:
    return list_transactions(db, user.id, limit=limit, offset=offset)

