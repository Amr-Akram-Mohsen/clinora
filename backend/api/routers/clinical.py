"""
api/routers/clinical.py

Endpoints for clinical consultations (SOAP notes), observations (vitals), and prescriptions.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from fastapi import status as http_status

from api.deps import ActiveUser, DbSession, get_request_context, require_roles
from api.schemas.clinical import (
    ObservationItemCreate,
    ObservationRead,
    PrescriptionItemCreate,
    PrescriptionRead,
    VisitCreate,
    VisitRead,
    VisitUpdate,
)
from application.auth.auth_service import RequestContext
from application.clinical.encounter_service import EncounterService

router = APIRouter(prefix="/visits", tags=["clinical"])


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
    response_model=VisitRead,
    status_code=http_status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("DOCTOR"))],
)
async def start_encounter(
    body: VisitCreate,
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> VisitRead:
    """Start a new consultation encounter."""
    service = EncounterService(session)
    ctx = _make_request_context(request)

    visit = await service.start_encounter(
        doctor=user,
        patient_id=body.patient_id,
        chief_complaint=body.chief_complaint,
        appointment_id=body.appointment_id,
        subjective_notes=body.subjective_notes,
        objective_notes=body.objective_notes,
        assessment_notes=body.assessment_notes,
        plan_notes=body.plan_notes,
        ctx=ctx,
    )
    return VisitRead.model_validate(visit)


@router.get(
    "/{visit_id}",
    response_model=VisitRead,
    dependencies=[Depends(require_roles("ADMIN", "DOCTOR", "NURSE"))],
)
async def get_encounter(
    visit_id: uuid.UUID,
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> VisitRead:
    """Retrieve full encounter record with observations and prescriptions."""
    service = EncounterService(session)
    ctx = _make_request_context(request)
    visit = await service.get_encounter(actor=user, visit_id=visit_id, ctx=ctx)
    return VisitRead.model_validate(visit)


@router.put(
    "/{visit_id}",
    response_model=VisitRead,
    dependencies=[Depends(require_roles("DOCTOR"))],
)
async def update_encounter_draft(
    visit_id: uuid.UUID,
    body: VisitUpdate,
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> VisitRead:
    """Update draft notes for an open encounter. Prohibited if already signed."""
    service = EncounterService(session)
    ctx = _make_request_context(request)

    visit = await service.update_draft(
        doctor=user,
        visit_id=visit_id,
        chief_complaint=body.chief_complaint,
        subjective_notes=body.subjective_notes,
        objective_notes=body.objective_notes,
        assessment_notes=body.assessment_notes,
        plan_notes=body.plan_notes,
        ctx=ctx,
    )
    return VisitRead.model_validate(visit)


@router.post(
    "/{visit_id}/sign",
    response_model=VisitRead,
    dependencies=[Depends(require_roles("DOCTOR"))],
)
async def sign_encounter(
    visit_id: uuid.UUID,
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> VisitRead:
    """Sign and permanently lock an encounter."""
    service = EncounterService(session)
    ctx = _make_request_context(request)
    visit = await service.sign_and_finalize(doctor=user, visit_id=visit_id, ctx=ctx)
    return VisitRead.model_validate(visit)


@router.post(
    "/{visit_id}/observations",
    response_model=list[ObservationRead],
    status_code=http_status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("DOCTOR", "NURSE"))],
)
async def record_visit_observations(
    visit_id: uuid.UUID,
    body: list[ObservationItemCreate],
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> list[ObservationRead]:
    """Record vitals/observations during a visit encounter."""
    service = EncounterService(session)
    ctx = _make_request_context(request)

    # First fetch visit to get patient_id
    visit = await service.get_encounter(actor=user, visit_id=visit_id, ctx=ctx)

    obs_data = [item.model_dump() for item in body]
    obs = await service.record_vitals(
        actor=user,
        patient_id=visit.patient_id,
        items=obs_data,
        visit_id=visit_id,
        ctx=ctx,
    )
    return [ObservationRead.model_validate(o) for o in obs]


@router.post(
    "/{visit_id}/prescriptions",
    response_model=list[PrescriptionRead],
    status_code=http_status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("DOCTOR"))],
)
async def issue_prescriptions(
    visit_id: uuid.UUID,
    body: list[PrescriptionItemCreate],
    request: Request,
    session: DbSession,
    user: ActiveUser,
) -> list[PrescriptionRead]:
    """Issue medications during an encounter."""
    service = EncounterService(session)
    ctx = _make_request_context(request)

    visit = await service.get_encounter(actor=user, visit_id=visit_id, ctx=ctx)

    items_data = [item.model_dump() for item in body]
    prescriptions = await service.issue_prescriptions(
        doctor=user,
        patient_id=visit.patient_id,
        visit_id=visit_id,
        items=items_data,
        ctx=ctx,
    )
    return [PrescriptionRead.model_validate(p) for p in prescriptions]
