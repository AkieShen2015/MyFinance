import asyncio

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finance import Account, Institution, Merchant, Transaction
from app.services.seed import seed_mock_data


def test_mock_seed_is_idempotent(session: Session) -> None:
    first = asyncio.run(seed_mock_data(session))
    second = asyncio.run(seed_mock_data(session))

    assert first.institutions == 14
    assert first.accounts == 15
    assert first.transactions > 100
    assert second.transactions == 0
    assert session.scalar(select(func.count()).select_from(Institution)) == 14
    assert session.scalar(select(func.count()).select_from(Account)) == 15
    assert session.scalar(select(func.count()).select_from(Transaction)) == first.transactions
    merchant_names = set(session.scalars(select(Merchant.display_name)).all())
    assert {
        "Canberra Cat Vet",
        "Kwafood 1982",
        "Yijia Asian Grocery",
        "ZhangLiang Malatang",
    }.issubset(merchant_names)
