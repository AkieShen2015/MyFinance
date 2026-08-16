import asyncio

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finance import Account, Institution, Transaction
from app.services.seed import seed_mock_data


def test_mock_seed_is_idempotent(session: Session) -> None:
    first = asyncio.run(seed_mock_data(session))
    second = asyncio.run(seed_mock_data(session))

    assert first.institutions == 2
    assert first.accounts == 3
    assert first.transactions > 100
    assert second.transactions == 0
    assert session.scalar(select(func.count()).select_from(Institution)) == 2
    assert session.scalar(select(func.count()).select_from(Account)) == 3
    assert session.scalar(select(func.count()).select_from(Transaction)) == first.transactions

