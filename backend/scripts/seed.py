"""
scripts/seed.py

Development/first-run database seeder.

Creates:
- Default organization (from SEED_ORG_NAME / SEED_ORG_SLUG env vars)
- Default roles: ADMIN, DOCTOR, NURSE, RECEPTIONIST
- Initial admin user (from SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD env vars)

Idempotent: re-running will not create duplicates if slug/email already exist.

Usage:
    cd backend
    python scripts/seed.py
"""

import asyncio
import os
import sys
from datetime import UTC, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ruff: noqa: E402
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings
from core.security import hash_password
from infrastructure.database.models.organization import Organization
from infrastructure.database.models.user import Role, User, UserRole

ROLES = [
    ("ADMIN", "Clinic administrator — manages users, settings, and operations"),
    ("DOCTOR", "Licensed physician — full clinical record access"),
    ("NURSE", "Nursing staff — clinical record access with limited write permissions"),
    ("RECEPTIONIST", "Front desk — appointment and patient registration access"),
]


async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session, session.begin():
        # --- Organization ---
        org_slug = os.getenv("SEED_ORG_SLUG", "clinora")
        org_name = os.getenv("SEED_ORG_NAME", "Clinora Clinic")

        org_stmt = select(Organization).where(Organization.slug == org_slug)
        org_result = await session.execute(org_stmt)
        org = org_result.scalar_one_or_none()

        if org is None:
            org = Organization(name=org_name, slug=org_slug, is_active=True)
            session.add(org)
            await session.flush()
            print(f"[seed] Created organization: {org_name} ({org_slug})")
        else:
            print(f"[seed] Organization already exists: {org_slug}")

        assert org is not None

        # --- Roles ---
        role_map: dict[str, Role] = {}
        for role_name, description in ROLES:
            role_stmt = select(Role).where(Role.name == role_name)
            role_result = await session.execute(role_stmt)
            role = role_result.scalar_one_or_none()

            if role is None:
                role = Role(name=role_name, description=description)
                session.add(role)
                await session.flush()
                print(f"[seed] Created role: {role_name}")
            else:
                print(f"[seed] Role already exists: {role_name}")

            role_map[role_name] = role

        # --- Admin user ---
        admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@clinora.com")
        admin_password = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!")
        admin_name = os.getenv("SEED_ADMIN_NAME", "System Administrator")

        user_stmt = select(User).where(User.email == admin_email)
        user_result = await session.execute(user_stmt)
        admin_user = user_result.scalar_one_or_none()

        if admin_user is None:
            admin_user = User(
                organization_id=org.id,
                email=admin_email,
                password_hash=hash_password(admin_password),
                full_name=admin_name,
                is_active=True,
                is_superuser=True,
            )
            session.add(admin_user)
            await session.flush()
            print(f"[seed] Created admin user: {admin_email}")

            # Assign ADMIN role
            admin_role = role_map.get("ADMIN")
            if admin_role:
                user_role = UserRole(
                    user_id=admin_user.id,
                    role_id=admin_role.id,
                    assigned_at=datetime.now(tz=UTC),
                    assigned_by=None,
                )
                session.add(user_role)
                await session.flush()
        else:
            print(f"[seed] Admin user already exists: {admin_email}")

    await engine.dispose()
    print("[seed] Done.")



if __name__ == "__main__":
    asyncio.run(seed())
