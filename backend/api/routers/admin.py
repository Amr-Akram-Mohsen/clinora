from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from api.deps import ActiveUser, DbSession, get_request_context, require_roles
from api.schemas.admin import (
    StaffListResponse,
    StaffInviteRequest,
    StaffUpdateRoleRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
    AuditLogListResponse,
)
from application.admin.admin_service import AdminService
from infrastructure.repositories.audit_repository import AuditRepository
from infrastructure.repositories.user_repository import UserRepository

router = APIRouter(prefix="/api/v1/admin", tags=["Administration"])


def get_admin_service(session: DbSession) -> AdminService:
    user_repo = UserRepository(session)
    audit_repo = AuditRepository(session)
    return AdminService(user_repo, audit_repo)


@router.get(
    "/staff",
    response_model=StaffListResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
)
def list_staff(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    role: Optional[str] = None,
    current_user: ActiveUser = None,
    admin_service: AdminService = Depends(get_admin_service),
):
    """List all staff members within the organization with optional search and role filters."""
    # Assuming the user model stores organization_id
    org_id = str(current_user.organization_id)
    return admin_service.list_staff(org_id=org_id, skip=skip, limit=limit, search=search, role=role)


@router.get(
    "/organization",
    response_model=OrganizationResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
)
def get_organization(
    current_user: ActiveUser = None,
    admin_service: AdminService = Depends(get_admin_service),
):
    """View clinic / organization profile settings."""
    org_id = str(current_user.organization_id)
    return admin_service.get_organization(org_id=org_id)


@router.put(
    "/organization",
    response_model=OrganizationResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
)
def update_organization(
    payload: OrganizationUpdateRequest,
    current_user: ActiveUser = None,
    admin_service: AdminService = Depends(get_admin_service),
    request_ctx: dict = Depends(get_request_context),
):
    """Update clinic profile settings and generate an audit trail record."""
    org_id = str(current_user.organization_id)
    update_data = payload.model_dump(exclude_unset=True)
    return admin_service.update_organization(
        org_id=org_id,
        update_data=update_data,
        actor_email=current_user.email,
        request_context=request_ctx,
    )


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_roles("ADMIN"))],
)
def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    outcome: Optional[str] = None,
    actor_email: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: ActiveUser = None,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Query immutable organization audit logs with advanced filtering."""
    org_id = str(current_user.organization_id)
    return admin_service.list_audit_logs(
        org_id=org_id,
        skip=skip,
        limit=limit,
        action=action,
        outcome=outcome,
        actor_email=actor_email,
        from_date=from_date,
        to_date=to_date,
    )