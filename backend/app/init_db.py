import asyncio

from app.db import engine
from app.models import Base


async def main():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
