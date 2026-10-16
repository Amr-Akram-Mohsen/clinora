"""
infrastructure/database/models/audit.py

ORM model for AuditLog — immutable business-event records.

Design decisions:
- Rows are NEVER updated. Once written, an audit record is permanent.
  The repository enforces this (no update method exists).
- organization_id is always populated for tenant-scoped audit queries.
- actor_id is nullable (SET NULL on user delete) but actor_email is
  denormalized as a snapshot so the audit record remains meaningful even
  if the user account is later deleted or anonymized.
- metadata is JSONB — used for structured context (resource details, changes)
  without embedding PHI unnecessarily.
- request_id links this audit event to the HTTP request log for correlation.

Indexes are designed for the actual audit query patterns:
- Tenant + time range (most common admin query)
- Actor lookup ("what did this user do?")
- Action filter ("show all logins")
- Resource trail ("audit trail for patient X")
- Request correlation ("find the audit event for request Y")
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class AuditLog(Base):
    """
    Immutable audit record. Every significant business action that needs to be
    traceable (auth events, clinical record access, data exports, AI usage, etc.)
    generates one of these.

    Written via AuditRepository — never via raw session.add() in route handlers.
    """

    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("ix_audit_logs_org_created", "organization_id", "created_at"),
        Index("ix_audit_logs_actor_id", "actor_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_request_id", "request_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=True,
    )
    # Nullable because system-generated events may have no actor.
    # SET NULL so records survive user deletion while remaining meaningful
    # via the actor_email snapshot.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Snapshot of email at event time — survives user deletion/anonymization
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Dot-namespaced action string: "user.login.success", "patient.viewed", etc.
    action: Mapped[str] = mapped_column(String(100), nullable=False)

    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # "success" | "failure"
    outcome: Mapped[str] = mapped_column(String(10), nullable=False)

    request_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured context — NEVER store raw PHI, passwords, or tokens here.
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action!r} "
            f"actor={self.actor_email!r} outcome={self.outcome!r}>"
        )
