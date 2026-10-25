"""
infrastructure/repositories/audit_repository.py

Repository for writing AuditLog records.

Responsibilities:
- Provide a single, controlled write path for audit events.
- Never update or delete audit records (immutability enforced here).
- Accept a structured AuditEvent dataclass so callers do not construct
  ORM objects directly.

Usage:
    from infrastructure.repositories.audit_repository import AuditRepository, AuditEvent

    repo = AuditRepository(session)
    await repo.record(AuditEvent(
        organization_id=org_id,
        actor_id=user.id,
        actor_email=user.email,
        action="user.login.success",
        outcome="success",
        request_id=request_id,
        ip_address=ip,
        user_agent=ua,
    ))
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models.audit import AuditLog


@dataclass
class AuditEvent:
    """
    Structured representation of an audit event.
    Passed to AuditRepository.record() — callers never construct AuditLog ORM
    objects directly, which ensures the immutability contract is maintained.
    """

    organization_id: uuid.UUID | None = None
    actor_email: str = "unknown"  # Snapshot — must be captured before any user mutation
    action: str = ""              # Dot-namespaced: "user.login.success"
    outcome: str = ""             # "success" | "failure"

    actor_id: uuid.UUID | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    request_id: uuid.UUID | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)



class AuditRepository:
    """
    Write-only repository for AuditLog.
    No update or delete methods exist by design.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, event: AuditEvent) -> AuditLog:
        """
        Persist an audit event.
        The session must be committed by the caller (typically the application
        service that owns the transaction for the surrounding operation).
        """
        log = AuditLog(
            organization_id=event.organization_id,
            actor_id=event.actor_id,
            actor_email=event.actor_email,
            action=event.action,
            outcome=event.outcome,
            resource_type=event.resource_type,
            resource_id=str(event.resource_id) if event.resource_id else None,
            request_id=event.request_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            metadata_=event.metadata,
            created_at=datetime.now(tz=UTC),
        )
        self._session.add(log)
        await self._session.flush()
        return log

    def find_logs(self, organization_id: str, skip: int = 0, limit: int = 50, action: Optional[str] = None, outcome: Optional[str] = None, actor_email: Optional[str] = None, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
        query = self._session.query(AuditLogModel).filter(AuditLogModel.organization_id == organization_id)
        if action:
            query = query.filter(AuditLogModel.action == action)
        if outcome:
            query = query.filter(AuditLogModel.outcome == outcome)
        if actor_email:
            query = query.filter(AuditLogModel.actor_email.ilike(f"%{actor_email}%"))
        if from_date:
            query = query.filter(AuditLogModel.created_at >= from_date)
        if to_date:
            query = query.filter(AuditLogModel.created_at <= to_date)
        return query.order_by(AuditLogModel.created_at.desc()).offset(skip).limit(limit).all()

    def count_logs(self, organization_id: str, action: Optional[str] = None, outcome: Optional[str] = None, actor_email: Optional[str] = None, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> int:
        query = self._session.query(AuditLogModel).filter(AuditLogModel.organization_id == organization_id)
        if action:
            query = query.filter(AuditLogModel.action == action)
        if outcome:
            query = query.filter(AuditLogModel.outcome == outcome)
        if actor_email:
            query = query.filter(AuditLogModel.actor_email.ilike(f"%{actor_email}%"))
        if from_date:
            query = query.filter(AuditLogModel.created_at >= from_date)
        if to_date:
            query = query.filter(AuditLogModel.created_at <= to_date)
        return query.count()