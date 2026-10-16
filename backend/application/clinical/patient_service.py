"""
application/clinical/patient_service.py

Patient management workflow orchestration:
- register_patient: Ingests demographics, verifies uniqueness, records patient, writes audit event.
- get_patient: Retrieves patient record and logs access audit.
- search_patients: Returns paginated search results within tenant.
- add_allergy: Records adverse reaction and writes audit event.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from application.auth.auth_service import RequestContext
from core.errors import ConflictError, NotFoundError, ValidationError
from infrastructure.database.models.patient import Allergy, Patient
from infrastructure.database.models.user import User
from infrastructure.repositories.audit_repository import AuditEvent, AuditRepository
from infrastructure.repositories.patient_repository import PatientRepository


class PatientService:
    """
    Orchestrates patient lifecycle workflows with audit logging.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._patients = PatientRepository(session)
        self._audit = AuditRepository(session)

    async def register_patient(
        self,
        actor: User,
        full_name: str,
        date_of_birth: date,
        gender: str,
        phone: str,
        ctx: RequestContext,
        national_id: str | None = None,
        blood_type: str | None = None,
        email: str | None = None,
        address: str | None = None,
        emergency_contact_name: str | None = None,
        emergency_contact_phone: str | None = None,
    ) -> Patient:
        """Register a new patient within the actor's organization."""
        if not full_name.strip():
            raise ValidationError("Full name is required.")
        if not phone.strip():
            raise ValidationError("Phone number is required.")

        patient = await self._patients.create(
            organization_id=actor.organization_id,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            phone=phone,
            national_id=national_id,
            blood_type=blood_type,
            email=email,
            address=address,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
        )

        await self._audit.record(
            AuditEvent(
                organization_id=actor.organization_id,
                actor_id=actor.id,
                actor_email=actor.email,
                action="patient.created",
                resource_type="patient",
                resource_id=str(patient.id),
                outcome="success",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                metadata={"patient_name": patient.full_name},
            )
        )

        return patient

    async def get_patient(
        self,
        actor: User,
        patient_id: uuid.UUID,
        ctx: RequestContext,
    ) -> Patient:
        """Fetch patient chart and record a view audit event."""
        patient = await self._patients.find_by_id(
            organization_id=actor.organization_id,
            patient_id=patient_id,
            include_allergies=True,
        )
        if not patient:
            raise NotFoundError(f"Patient with ID {patient_id} not found.")

        await self._audit.record(
            AuditEvent(
                organization_id=actor.organization_id,
                actor_id=actor.id,
                actor_email=actor.email,
                action="patient.viewed",
                resource_type="patient",
                resource_id=str(patient.id),
                outcome="success",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
            )
        )

        return patient

    async def search_patients(
        self,
        actor: User,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Patient], int]:
        """Search patients within the actor's organization."""
        return await self._patients.search(
            organization_id=actor.organization_id,
            query=query,
            limit=limit,
            offset=offset,
        )

    async def add_allergy(
        self,
        actor: User,
        patient_id: uuid.UUID,
        allergen: str,
        severity: str,
        ctx: RequestContext,
        reaction: str | None = None,
    ) -> Allergy:
        """Document a verified allergy on the patient chart."""
        # Verify patient exists
        patient = await self._patients.find_by_id(
            organization_id=actor.organization_id,
            patient_id=patient_id,
            include_allergies=False,
        )
        if not patient:
            raise NotFoundError(f"Patient with ID {patient_id} not found.")

        allergy = await self._patients.add_allergy(
            organization_id=actor.organization_id,
            patient_id=patient_id,
            allergen=allergen,
            severity=severity,
            reaction=reaction,
        )

        await self._audit.record(
            AuditEvent(
                organization_id=actor.organization_id,
                actor_id=actor.id,
                actor_email=actor.email,
                action="allergy.recorded",
                resource_type="allergy",
                resource_id=str(allergy.id),
                outcome="success",
                request_id=ctx.request_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                metadata={"allergen": allergen, "severity": severity, "patient_id": str(patient_id)},
            )
        )

        return allergy
