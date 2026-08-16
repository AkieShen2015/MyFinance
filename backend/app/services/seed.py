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
from app.services.categorisation import category_id_from_saved_rules
from app.services.transaction_processing import normalise_description, normalise_merchant

SYSTEM_CATEGORIES: dict[str, tuple[CategoryType, tuple[str, ...]]] = {
    "Food & Restaurant": (CategoryType.EXPENSE, ()),
    "Groceries": (CategoryType.EXPENSE, ()),
    "Takeaway": (CategoryType.EXPENSE, ()),
    "Transport": (CategoryType.EXPENSE, ("Fuel", "Public Transport", "Rideshare")),
    "Housing": (CategoryType.EXPENSE, ("Rent", "Mortgage", "Utilities")),
    "Pet": (CategoryType.EXPENSE, ()),
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
    "Restaurants": "Food & Restaurant",
    "Public Transport": "Public Transport",
    "Fuel": "Fuel",
    "Interest": "Interest",
    "Pet Supplies": "Pet",
    "Veterinary": "Pet",
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
            Category.user_id.is_(None),
            Category.parent_id == (parent.id if parent else None),
            Category.name == name,
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
            categories[child_name] = child
    return categories


def _merchant_for_description(
    session: Session, description: str, cache: dict[str, Merchant]
) -> Merchant:
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
    identity = normalise_merchant(description)
    merchant = cache.get(identity.canonical_name)
    if merchant is None:
        merchant = session.scalar(
            select(Merchant).where(Merchant.canonical_name == identity.canonical_name)
        )
    if merchant is None:
        merchant = Merchant(
            canonical_name=identity.canonical_name,
            display_name=identity.display_name,
            merchant_type=identity.merchant_type,
        )
        session.add(merchant)
        session.flush()
    cache[identity.canonical_name] = merchant
    return merchant


async def seed_mock_data(session: Session, email: str = "demo@example.com") -> SeedResult:
    provider = MockBankProvider()
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email.lower())
        session.add(user)
        session.flush()

    categories = seed_system_categories(session)
    institutions: dict[str, Institution] = {}
    for provider_institution in await provider.get_institutions():
        institution = session.scalar(
            select(Institution).where(
                Institution.provider == provider.name,
                Institution.external_id == provider_institution.external_id,
            )
        )
        if institution is None:
            institution = Institution(
                provider=provider.name,
                external_id=provider_institution.external_id,
                name=provider_institution.name,
                logo_url=provider_institution.logo_url,
                country=provider_institution.country,
            )
            session.add(institution)
            session.flush()
        institutions[provider_institution.external_id] = institution

    accounts: dict[str, Account] = {}
    for connection_id in await provider.get_connections("demo-user"):
        institution_external_id = f"mock-{connection_id.rsplit(':', maxsplit=1)[-1]}"
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
        for provider_account in await provider.get_accounts(connection_id):
            account = session.scalar(
                select(Account).where(
                    Account.user_id == user.id,
                    Account.external_account_id == provider_account.external_id,
                )
            )
            if account is None:
                account = Account(
                    user_id=user.id,
                    bank_connection_id=connection.id,
                    institution_id=institution.id,
                    external_account_id=provider_account.external_id,
                    account_name=provider_account.name,
                    account_type=provider_account.account_type,
                    masked_account_number=provider_account.masked_account_number,
                    currency=provider_account.currency,
                    current_balance=provider_account.current_balance,
                    available_balance=provider_account.available_balance,
                )
                session.add(account)
                session.flush()
            else:
                account.bank_connection_id = connection.id
                account.institution_id = institution.id
                account.account_name = provider_account.name
                account.account_type = provider_account.account_type
                account.masked_account_number = provider_account.masked_account_number
                account.currency = provider_account.currency
                account.current_balance = provider_account.current_balance
                account.available_balance = provider_account.available_balance
            accounts[provider_account.external_id] = account

    inserted = 0
    merchant_cache: dict[str, Merchant] = {}
    for external_account_id, account in accounts.items():
        cursor: str | None = None
        while True:
            page = await provider.get_transactions(external_account_id, cursor)
            for provider_transaction in page.transactions:
                existing = session.scalar(
                    select(Transaction).where(
                        Transaction.account_id == account.id,
                        Transaction.external_transaction_id
                        == provider_transaction.external_id,
                    )
                )
                if existing is not None:
                    merchant = _merchant_for_description(
                        session, provider_transaction.description, merchant_cache
                    )
                    existing.description = provider_transaction.description
                    existing.normalised_description = normalise_description(
                        provider_transaction.description
                    ).value
                    existing.merchant_id = merchant.id
                    saved_category_id = category_id_from_saved_rules(
                        session,
                        user.id,
                        account_id=account.id,
                        merchant_id=merchant.id,
                        normalised_description=existing.normalised_description,
                        provider_category=provider_transaction.provider_category,
                    )
                    if saved_category_id is not None:
                        existing.category_id = saved_category_id
                    continue
                merchant = _merchant_for_description(
                    session, provider_transaction.description, merchant_cache
                )
                normalised_description = normalise_description(
                    provider_transaction.description
                ).value
                category_name = PROVIDER_CATEGORY_MAP.get(
                    provider_transaction.provider_category or "", "Other"
                )
                saved_category_id = category_id_from_saved_rules(
                    session,
                    user.id,
                    account_id=account.id,
                    merchant_id=merchant.id,
                    normalised_description=normalised_description,
                    provider_category=provider_transaction.provider_category,
                )
                session.add(
                    Transaction(
                        account_id=account.id,
                        external_transaction_id=provider_transaction.external_id,
                        transaction_date=provider_transaction.transaction_date,
                        posted_date=provider_transaction.posted_date,
                        description=provider_transaction.description,
                        normalised_description=normalised_description,
                        merchant_id=merchant.id,
                        amount=provider_transaction.amount,
                        currency=provider_transaction.currency,
                        transaction_type=provider_transaction.transaction_type,
                        category_id=saved_category_id or categories[category_name].id,
                        status=provider_transaction.status,
                        pending=provider_transaction.status.value == "pending",
                        provider_category=provider_transaction.provider_category,
                        raw_data={
                            "source": "mock",
                            "fixture_id": provider_transaction.external_id,
                        },
                    )
                )
                inserted += 1
            if page.next_cursor is None:
                break
            cursor = page.next_cursor

    session.commit()
    return SeedResult(len(institutions), len(accounts), inserted)
