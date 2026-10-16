"""
api/routers/patients.py

Endpoints for Patient Master Index, demographics, and allergies.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi import status as http_status

from api.deps import ActiveUser, DbSession, get_request_context, require_roles
from api.schemas.clinical import ObservationRead, PrescriptionRead, VisitListItem
from api.schemas.common import PaginatedResponse
from api.schemas.patient import AllergyCreate, AllergyRead, PatientCreate, PatientListItem, PatientRead
from application.auth.auth_service import RequestContext
from application.clinical.patient_service import PatientService
from infrastructure.repositories.clinical_repository import ClinicalRepository

router = APIRouter(prefix="/patients", tags=["patients"])


def _make_request_context(request: Request) -> RequestContext:
    ctx_dict = get_request_context(request)
    request_id = ctx_dict.get("request_id")
    return RequestContext(
        request_id=uuid.UUID(request_id) if request_id else None,
        ip_address=ctx_dict.get("ip_address"),
        user_agent=ctx_dict.get("user_agent"),
    )


@router.post(
    "",
    response_model=PatientRead,
    status_code=http_status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"))],
)
async def create_patient(
    body: PatientCreate,
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> PatientRead:
    """Register a new patient into the clinic organization."""
    service = PatientService(session)
    ctx = _make_request_context(request)

    patient = await service.register_patient(
        actor=user,
        full_name=body.full_name,
        date_of_birth=body.date_of_birth,
        gender=body.gender,
        phone=body.phone,
        ctx=ctx,
        national_id=body.national_id,
        blood_type=body.blood_type,
        email=body.email,
        address=body.address,
        emergency_contact_name=body.emergency_contact_name,
        emergency_contact_phone=body.emergency_contact_phone,
    )
    return PatientRead.model_validate(patient)


@router.get(
    "",
    response_model=PaginatedResponse[PatientListItem],
    dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"))],
)
async def list_patients(
    session: DbSession,
    user: ActiveUser,
    q: Annotated[str | None, Query(description="Search by name, phone, or national ID")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[PatientListItem]:
    """Search and list active patients in the clinic with pagination."""
    service = PatientService(session)
    offset = (page - 1) * page_size
    items, total = await service.search_patients(
        actor=user,
        query=q,
        limit=page_size,
        offset=offset,
    )

    item_schemas = [PatientListItem.model_validate(p) for p in items]
    return PaginatedResponse.create(
        items=item_schemas,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientRead,
    dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE", "RECEPTIONIST"))],
)
async def get_patient_profile(
    patient_id: uuid.UUID,
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> PatientRead:
    """Retrieve full patient chart with allergies."""
    service = PatientService(session)
    ctx = _make_request_context(request)
    patient = await service.get_patient(actor=user, patient_id=patient_id, ctx=ctx)
    return PatientRead.model_validate(patient)


@router.post(
    "/{patient_id}/allergies",
    response_model=AllergyRead,
    status_code=http_status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE"))],
)
async def record_allergy(
    patient_id: uuid.UUID,
    body: AllergyCreate,
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> AllergyRead:
    """Document a verified allergy on the patient chart."""
    service = PatientService(session)
    ctx = _make_request_context(request)
    allergy = await service.add_allergy(
        actor=user,
        patient_id=patient_id,
        allergen=body.allergen,
        severity=body.severity,
        reaction=body.reaction,
        ctx=ctx,
    )
    return AllergyRead.model_validate(allergy)


@router.get(
    "/{patient_id}/visits",
    response_model=PaginatedResponse[VisitListItem],
    dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE"))],
)
async def list_patient_visits(
    patient_id: uuid.UUID,
    session: DbSession,
    user: ActiveUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> PaginatedResponse[VisitListItem]:
    """Retrieve chronological visits for a patient."""
    repo = ClinicalRepository(session)
    offset = (page - 1) * page_size
    visits, total = await repo.list_patient_visits(
        organization_id=user.organization_id,
        patient_id=patient_id,
        limit=page_size,
        offset=offset,
    )
    items = [VisitListItem.model_validate(v) for v in visits]
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{patient_id}/observations",
    response_model=list[ObservationRead],
    dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE"))],
)
async def list_patient_observations(
    patient_id: uuid.UUID,
    session: DbSession,
    user: ActiveUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ObservationRead]:
    """Retrieve recent vitals and observations for a patient."""
    repo = ClinicalRepository(session)
    obs = await repo.list_patient_observations(
        organization_id=user.organization_id,
        patient_id=patient_id,
        limit=limit,
    )
    return [ObservationRead.model_validate(o) for o in obs]


@router.get(
    "/{patient_id}/prescriptions",
    response_model=list[PrescriptionRead],
    dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE"))],
)
async def list_patient_prescriptions(
    patient_id: uuid.UUID,
    session: DbSession,
    user: ActiveUser,
    active_only: Annotated[bool, Query()] = False,
) -> list[PrescriptionRead]:
    """Retrieve prescriptions for a patient."""
    repo = ClinicalRepository(session)
    prescriptions = await repo.list_patient_prescriptions(
        organization_id=user.organization_id,
        patient_id=patient_id,
        active_only=active_only,
    )
    return [PrescriptionRead.model_validate(p) for p in prescriptions]
