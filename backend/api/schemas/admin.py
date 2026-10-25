from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


# --- Staff Schemas ---
class StaffUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    roles: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StaffInviteRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: str = Field(..., description="ADMIN, DOCTOR, NURSE, or RECEPTIONIST")


class StaffUpdateRoleRequest(BaseModel):
    role: str


class StaffListResponse(BaseModel):
    total: int
    items: List[StaffUserResponse]


# --- Clinic Settings Schemas ---
class OrganizationResponse(BaseModel):
    id: str
    name: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    operating_schedule: Optional[Dict[str, Any]] = None


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    address: Optional[str] = None
    operating_schedule: Optional[Dict[str, Any]] = None


# --- Audit Log Schemas ---
class AuditLogResponse(BaseModel):
    id: str
    action: str
    outcome: str
    actor_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogResponse]