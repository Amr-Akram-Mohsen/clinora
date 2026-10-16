"""
infrastructure/database/base.py

SQLAlchemy declarative base and reusable ORM mixins.

Responsibilities:
- Provide the single DeclarativeBase subclass shared by all ORM models.
- Provide UUIDPKMixin and TimestampMixin used by every table.

Design:
- UUID primary keys use server-side gen (gen_random_uuid()) as default so
  that IDs are valid even before a DB round-trip.
- Timestamps are TIMESTAMPTZ (timezone-aware). All datetimes stored in UTC.
- `updated_at` is set to server_default but also uses onupdate for ORM-driven
  updates. Note: bulk UPDATE statements bypass onupdate — services must handle
  that explicitly where needed.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all Clinora ORM models."""


class UUIDPKMixin:
    """
    Adds a UUID primary key column `id`.
    Server default generates the UUID in PostgreSQL; Python default is also
    set so the object has a valid `id` immediately after instantiation.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """
    Adds `created_at` and `updated_at` TIMESTAMPTZ columns.
    Both use database server defaults (now()) so they are consistent
    regardless of whether the insert was done via ORM or raw SQL.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
