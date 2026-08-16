from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import AccountType, ConnectionStatus, TransactionType
from app.models.finance import Account, BankConnection, Institution, Transaction, User


def test_duplicate_external_transaction_is_rejected(session: Session) -> None:
    user = User(email="owner@example.com")
    institution = Institution(
        provider="mock", external_id="bank-1", name="Example Bank", country="AU"
    )
    session.add_all((user, institution))
    session.flush()
    connection = BankConnection(
        user_id=user.id,
        institution_id=institution.id,
        provider="mock",
        provider_connection_id="connection-1",
        status=ConnectionStatus.ACTIVE,
    )
    session.add(connection)
    session.flush()
    account = Account(
        user_id=user.id,
        bank_connection_id=connection.id,
        institution_id=institution.id,
        external_account_id="account-1",
        account_name="Everyday",
        account_type=AccountType.TRANSACTION,
        currency="AUD",
        current_balance=Decimal("100.00"),
    )
    session.add(account)
    session.flush()

    values = {
        "account_id": account.id,
        "external_transaction_id": "transaction-1",
        "transaction_date": date(2026, 8, 1),
        "description": "TEST TRANSACTION",
        "amount": Decimal("-10.00"),
        "currency": "AUD",
        "transaction_type": TransactionType.EXPENSE,
    }
    session.add(Transaction(**values))
    session.commit()
    session.add(Transaction(**values))

    with pytest.raises(IntegrityError):
        session.commit()


def test_same_external_id_is_allowed_for_different_accounts(session: Session) -> None:
    constraint = next(
        item
        for item in Transaction.__table__.constraints
        if getattr(item, "name", None) == "uq_transaction_account_external"
    )
    assert [column.name for column in constraint.columns] == [
        "account_id",
        "external_transaction_id",
    ]

