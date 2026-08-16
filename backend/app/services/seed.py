from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.banking.mock_provider import MockBankProvider
from app.models.enums import CategoryType, ConnectionStatus
from app.models.finance import (
    Account,
    BankConnection,
    Category,
    Institution,
    Merchant,
    Transaction,
    User,
)


SYSTEM_CATEGORIES: dict[str, tuple[CategoryType, tuple[str, ...]]] = {
    "Food": (CategoryType.EXPENSE, ("Groceries", "Restaurants", "Takeaway")),
    "Transport": (CategoryType.EXPENSE, ("Fuel", "Public Transport", "Rideshare")),
    "Housing": (CategoryType.EXPENSE, ("Rent", "Mortgage", "Utilities")),
    "Pet": (CategoryType.EXPENSE, ("Vet", "Food", "Medication", "Insurance", "Supplies")),
    "Shopping": (CategoryType.EXPENSE, ("Electronics",)),
    "Health": (CategoryType.EXPENSE, ("Fitness",)),
    "Subscriptions": (CategoryType.EXPENSE, ()),
    "Income": (CategoryType.INCOME, ("Salary", "Interest", "Other Income")),
    "Other": (CategoryType.EXPENSE, ()),
}

PROVIDER_CATEGORY_MAP = {
    "Salary": "Salary",
    "Rent": "Rent",
    "Groceries": "Groceries",
    "Subscriptions": "Subscriptions",
    "Fitness": "Fitness",
    "Utilities": "Utilities",
    "Restaurants": "Restaurants",
    "Public Transport": "Public Transport",
    "Fuel": "Fuel",
    "Interest": "Interest",
    "Pet Supplies": "Supplies",
    "Veterinary": "Vet",
    "Electronics": "Electronics",
}

MERCHANTS = {
    "WOOLWORTHS": ("woolworths", "Woolworths", "supermarket"),
    "NETFLIX": ("netflix", "Netflix", "subscription"),
    "SPOTIFY": ("spotify", "Spotify", "subscription"),
    "ICLOUD": ("apple-icloud", "Apple iCloud", "subscription"),
    "FITNESS FIRST": ("fitness-first", "Fitness First", "fitness"),
    "ENERGY AUSTRALIA": ("energy-australia", "EnergyAustralia", "utility"),
    "HARBOUR DINING": ("harbour-dining", "Harbour Dining", "restaurant"),
    "TRANSPORT NSW": ("transport-nsw", "Transport for NSW", "transport"),
    "SHELL": ("shell", "Shell", "fuel"),
    "PETBARN": ("petbarn", "Petbarn", "pet"),
    "ANIMAL HOSPITAL": ("sydney-animal-hospital", "Sydney Animal Hospital", "vet"),
    "GOOD GUYS": ("the-good-guys", "The Good Guys", "retail"),
    "ACME": ("acme-employer", "ACME Pty Ltd", "employer"),
}


@dataclass(frozen=True)
class SeedResult:
    institutions: int
    accounts: int
    transactions: int


def _get_or_create_category(
    session: Session,
    name: str,
    category_type: CategoryType,
    parent: Category | None = None,
) -> Category:
    category = session.scalar(
        select(Category).where(
            Category.user_id.is_(None), Category.parent_id == (parent.id if parent else None), Category.name == name
        )
    )
    if category is None:
        category = Category(
            name=name,
            type=category_type,
            parent=parent,
            is_system=True,
            user_id=None,
        )
        session.add(category)
        session.flush()
    return category


def seed_system_categories(session: Session) -> dict[str, Category]:
    categories: dict[str, Category] = {}
    for parent_name, (category_type, children) in SYSTEM_CATEGORIES.items():
        parent = _get_or_create_category(session, parent_name, category_type)
        categories[parent_name] = parent
        for child_name in children:
            child = _get_or_create_category(session, child_name, category_type, parent)
            categories[child_name if child_name != "Food" else "Pet Food"] = child
    return categories


def _merchant_for_description(
    session: Session, description: str, cache: dict[str, Merchant]
) -> Merchant | None:
    upper_description = description.upper()
    for match, (canonical_name, display_name, merchant_type) in MERCHANTS.items():
        if match not in upper_description:
            continue
        merchant = cache.get(canonical_name)
        if merchant is None:
            merchant = session.scalar(
                select(Merchant).where(Merchant.canonical_name == canonical_name)
            )
        if merchant is None:
            merchant = Merchant(
                canonical_name=canonical_name,
                display_name=display_name,
                merchant_type=merchant_type,
            )
            session.add(merchant)
            session.flush()
        cache[canonical_name] = merchant
        return merchant
    return None


async def seed_mock_data(session: Session, email: str = "demo@example.com") -> SeedResult:
    provider = MockBankProvider()
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email.lower())
        session.add(user)
        session.flush()

    categories = seed_system_categories(session)
    institutions: dict[str, Institution] = {}
    for item in await provider.get_institutions():
        institution = session.scalar(
            select(Institution).where(
                Institution.provider == provider.name, Institution.external_id == item.external_id
            )
        )
        if institution is None:
            institution = Institution(
                provider=provider.name,
                external_id=item.external_id,
                name=item.name,
                logo_url=item.logo_url,
                country=item.country,
            )
            session.add(institution)
            session.flush()
        institutions[item.external_id] = institution

    accounts: dict[str, Account] = {}
    for connection_id in await provider.get_connections("demo-user"):
        institution_external_id = "mock-anz" if connection_id.endswith(":anz") else "mock-commbank"
        institution = institutions[institution_external_id]
        connection = session.scalar(
            select(BankConnection).where(
                BankConnection.provider == provider.name,
                BankConnection.provider_connection_id == connection_id,
            )
        )
        if connection is None:
            connection = BankConnection(
                user_id=user.id,
                institution_id=institution.id,
                provider=provider.name,
                provider_connection_id=connection_id,
                status=ConnectionStatus.ACTIVE,
                last_sync_at=datetime.now(UTC),
                consent_expires_at=datetime.now(UTC) + timedelta(days=365),
            )
            session.add(connection)
            session.flush()
        for item in await provider.get_accounts(connection_id):
            account = session.scalar(
                select(Account).where(
                    Account.bank_connection_id == connection.id,
                    Account.external_account_id == item.external_id,
                )
            )
            if account is None:
                account = Account(
                    user_id=user.id,
                    bank_connection_id=connection.id,
                    institution_id=institution.id,
                    external_account_id=item.external_id,
                    account_name=item.name,
                    account_type=item.account_type,
                    masked_account_number=item.masked_account_number,
                    currency=item.currency,
                    current_balance=item.current_balance,
                    available_balance=item.available_balance,
                )
                session.add(account)
                session.flush()
            accounts[item.external_id] = account

    inserted = 0
    merchant_cache: dict[str, Merchant] = {}
    for external_account_id, account in accounts.items():
        cursor: str | None = None
        while True:
            page = await provider.get_transactions(external_account_id, cursor)
            for item in page.transactions:
                exists = session.scalar(
                    select(Transaction.id).where(
                        Transaction.account_id == account.id,
                        Transaction.external_transaction_id == item.external_id,
                    )
                )
                if exists is not None:
                    continue
                merchant = _merchant_for_description(session, item.description, merchant_cache)
                category_name = PROVIDER_CATEGORY_MAP.get(item.provider_category or "", "Other")
                session.add(
                    Transaction(
                        account_id=account.id,
                        external_transaction_id=item.external_id,
                        transaction_date=item.transaction_date,
                        posted_date=item.posted_date,
                        description=item.description,
                        normalised_description=item.description.upper(),
                        merchant_id=merchant.id if merchant else None,
                        amount=item.amount,
                        currency=item.currency,
                        transaction_type=item.transaction_type,
                        category_id=categories[category_name].id,
                        status=item.status,
                        pending=item.status.value == "pending",
                        provider_category=item.provider_category,
                        raw_data={"source": "mock", "fixture_id": item.external_id},
                    )
                )
                inserted += 1
            if page.next_cursor is None:
                break
            cursor = page.next_cursor

    session.commit()
    return SeedResult(len(institutions), len(accounts), inserted)

