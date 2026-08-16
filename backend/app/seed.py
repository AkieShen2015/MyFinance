import asyncio

from app.core.database import SessionLocal
from app.services.seed import seed_mock_data


async def main() -> None:
    with SessionLocal() as session:
        result = await seed_mock_data(session)
    print(
        f"Seed complete: {result.institutions} institutions, "
        f"{result.accounts} accounts, {result.transactions} new transactions"
    )


if __name__ == "__main__":
    asyncio.run(main())

