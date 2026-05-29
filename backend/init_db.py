import asyncio
from sqlalchemy import text
from app.database import engine, Base, async_session
from app.models import *
from app.models.user import User, PlatformRole
from app.utils.security import hash_password


async def apply_migrations(conn):
    await conn.execute(
        text(
            """
            DO $$
            BEGIN
                CREATE TYPE organizationcategory AS ENUM (
                    'it','marketing','hr','finance','sales','education','healthcare','nonprofit','other'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE organizations
                ADD COLUMN IF NOT EXISTS category organizationcategory NOT NULL DEFAULT 'other',
                ADD COLUMN IF NOT EXISTS data JSONB;
            """
        )
    )
    await conn.execute(
        text(
            """
            ALTER TABLE board_columns
                ADD COLUMN IF NOT EXISTS is_confirmed BOOLEAN NOT NULL DEFAULT FALSE;
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action VARCHAR NOT NULL,
                entity_type VARCHAR NOT NULL,
                entity_id VARCHAR,
                details VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
            """
        )
    )


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await apply_migrations(conn)

    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@ocs.local",
                username="admin",
                hashed_password=hash_password("admin123"),
                full_name="Администратор",
                platform_role=PlatformRole.ADMIN,
            )
            session.add(admin)
            await session.commit()
            print("Admin user created: admin / admin123")
        else:
            print("Admin user already exists")


if __name__ == "__main__":
    asyncio.run(init())
