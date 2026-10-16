"""
infrastructure/database/models/organization.py

ORM model for Organization (clinic/tenant).

Purpose:
- Represents a single clinic or organization using the platform.
- Every user, patient, appointment, and clinical record belongs to exactly
  one organization, providing the fundamental tenancy boundary.
- Phase 1 operates with a single organization; multi-clinic management UI
  is deferred to Phase 3. The data model is correct from the start.

Constraints:
- slug must be unique (used as a short human-readable identifier).
- Deletion is restricted: organizations should be archived, not deleted, once
  any clinical data is associated.
"""


from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database.base import Base, TimestampMixin, UUIDPKMixin


class Organization(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships (back-populated from User)
    users: Mapped[list["User"]] = relationship("User", back_populates="organization")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug!r}>"


# Avoid circular import — imported after class definition
from infrastructure.database.models.user import User  # noqa: E402, F401
