"""
infrastructure/repositories/patient_repository.py

Repository for Patient and Allergy database queries.
Strictly enforces organization_id tenant scoping on every operation.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from infrastructure.database.models.patient import Allergy, Patient


class PatientRepository:
    """
    Data access for Patient and Allergy entities within an organization tenant boundary.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        organization_id: uuid.UUID,
        full_name: str,
        date_of_birth: date,
        gender: str,
        phone: str,
        national_id: str | None = None,
        blood_type: str | None = None,
        email: str | None = None,
        address: str | None = None,
        emergency_contact_name: str | None = None,
        emergency_contact_phone: str | None = None,
    ) -> Patient:
        """Create and persist a new patient within the organization."""
        patient = Patient(
            organization_id=organization_id,
            full_name=full_name.strip(),
            date_of_birth=date_of_birth,
            gender=gender.upper().strip(),
            phone=phone.strip(),
            national_id=national_id.strip() if national_id else None,
            blood_type=blood_type.strip() if blood_type else None,
            email=email.strip().lower() if email else None,
            address=address.strip() if address else None,
            emergency_contact_name=emergency_contact_name.strip() if emergency_contact_name else None,
            emergency_contact_phone=emergency_contact_phone.strip() if emergency_contact_phone else None,
        )
        self._session.add(patient)
        await self._session.flush()
        return patient

    async def find_by_id(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
        include_allergies: bool = True,
    ) -> Patient | None:
        """Find a patient by ID, strictly scoped to the tenant organization."""
        stmt = (
            select(Patient)
            .where(
                Patient.id == patient_id,
                Patient.organization_id == organization_id,
                Patient.is_active.is_(True),
            )
        )
        if include_allergies:
            stmt = stmt.options(selectinload(Patient.allergies))

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        organization_id: uuid.UUID,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Patient], int]:
        """
        Search active patients within an organization by name, phone, or national ID.
        Returns a tuple of (results, total_count).
        """
        base_filter = [
            Patient.organization_id == organization_id,
            Patient.is_active.is_(True),
        ]

        if query and query.strip():
            clean_q = f"%{query.strip()}%"
            base_filter.append(
                or_(
                    Patient.full_name.ilike(clean_q),
                    Patient.phone.ilike(clean_q),
                    Patient.national_id.ilike(clean_q),
                )
            )

        # Count total matches
        count_stmt = select(func.count(Patient.id)).where(*base_filter)
        total_count = (await self._session.execute(count_stmt)).scalar_one()

        # Fetch page
        stmt = (
            select(Patient)
            .where(*base_filter)
            .order_by(Patient.full_name.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total_count

    async def add_allergy(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
        allergen: str,
        severity: str,
        reaction: str | None = None,
    ) -> Allergy:
        """Record a documented allergy for a patient."""
        allergy = Allergy(
            organization_id=organization_id,
            patient_id=patient_id,
            allergen=allergen.strip(),
            severity=severity.upper().strip(),
            reaction=reaction.strip() if reaction else None,
        )
        self._session.add(allergy)
        await self._session.flush()
        return allergy

    async def list_allergies(
        self,
        organization_id: uuid.UUID,
        patient_id: uuid.UUID,
    ) -> list[Allergy]:
        """List all documented allergies for a patient."""
        stmt = (
            select(Allergy)
            .where(
                Allergy.organization_id == organization_id,
                Allergy.patient_id == patient_id,
            )
            .order_by(Allergy.recorded_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
