"""infrastructure/database/models — ORM model registry."""

# Import all models here so that Alembic's env.py sees them when it
# imports infrastructure.database.models before generating migrations.
from infrastructure.database.models.audit import AuditLog
from infrastructure.database.models.clinical import Appointment, Observation, Prescription, Visit
from infrastructure.database.models.organization import Organization
from infrastructure.database.models.patient import Allergy, Patient
from infrastructure.database.models.user import RefreshToken, Role, User, UserRole

__all__ = [
    "Organization",
    "User",
    "Role",
    "UserRole",
    "RefreshToken",
    "AuditLog",
    "Patient",
    "Allergy",
    "Appointment",
    "Visit",
    "Observation",
    "Prescription",
]
