"""Migrate child PINs from plaintext storage to password-style hashes.

Run once against a backed-up production database:

    python3 -m migrations.migrate_child_pins

The migration is safe to rerun after a partial deployment. It only removes the
legacy plaintext column after every child has a hash.
"""

import asyncio

from sqlalchemy import text

from auth import hash_password
from database import engine


async def migrate() -> None:
    async with engine.begin() as connection:
        columns = await connection.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'children'
                  AND column_name IN ('pin', 'pin_hash')
                """
            )
        )
        existing_columns = {row[0] for row in columns}

        if "pin_hash" not in existing_columns:
            await connection.execute(
                text("ALTER TABLE children ADD COLUMN pin_hash VARCHAR(255)")
            )

        if "pin" in existing_columns:
            children = await connection.execute(
                text("SELECT id, pin FROM children WHERE pin_hash IS NULL")
            )
            for child_id, pin in children:
                await connection.execute(
                    text(
                        "UPDATE children SET pin_hash = :pin_hash "
                        "WHERE id = :child_id"
                    ),
                    {"child_id": child_id, "pin_hash": hash_password(pin)},
                )

        missing_hashes = await connection.execute(
            text("SELECT COUNT(*) FROM children WHERE pin_hash IS NULL")
        )
        if missing_hashes.scalar_one() != 0:
            raise RuntimeError("Migration stopped: one or more children lack a PIN hash")

        await connection.execute(
            text("ALTER TABLE children ALTER COLUMN pin_hash SET NOT NULL")
        )

        if "pin" in existing_columns:
            await connection.execute(text("ALTER TABLE children DROP COLUMN pin"))

    await engine.dispose()
    print("Child PIN migration completed successfully.")


if __name__ == "__main__":
    asyncio.run(migrate())
