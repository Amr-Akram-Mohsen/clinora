from datetime import datetime
from fastapi import HTTPException, status
from typing import Optional
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.repositories.audit_repository import AuditRepository

class AdminService:
    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository):
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    def list_staff(self, org_id: str, skip: int = 0, limit: int = 20, search: Optional[str] = None, role: Optional[str] = None):
        items = self.user_repo.find_staff_by_org(org_id, skip, limit, search, role)
        total = self.user_repo.count_staff_by_org(org_id, search, role)
        return {"items": items, "total": total}

    def update_staff_role(self, org_id: str, user_id: str, new_role: str, current_user_id: str):
        if user_id == current_user_id and new_role != "ADMIN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote yourself from admin role.")
        # Perform role update logic here...
        return {"message": "Role updated successfully"}

    def toggle_staff_status(self, org_id: str, user_id: str, is_active: bool, current_user_id: str):
        if user_id == current_user_id and not is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate your own account.")
        # Perform deactivation/activation logic here...
        return {"message": f"Account status updated to {is_active}"}

    def get_organization(self, org_id: str):
        org = self.user_repo.find_organization_by_id(org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        return org

    def update_organization(self, org_id: str, update_data: dict, actor_email: str):
        org = self.get_organization(org_id)
        for key, value in update_data.items():
            if value is not None:
                setattr(org, key, value)
        # Commit changes & record audit log event "organization.update"
        return org

    def list_audit_logs(self, org_id: str, skip: int = 0, limit: int = 50, action: Optional[str] = None, outcome: Optional[str] = None, actor_email: Optional[str] = None, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None):
        items = self.audit_repo.find_logs(org_id, skip, limit, action, outcome, actor_email, from_date, to_date)
        total = self.audit_repo.count_logs(org_id, action, outcome, actor_email, from_date, to_date)
        return {"items": items, "total": total}