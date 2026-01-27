from fastapi import APIRouter, HTTPException
from bot.schemas.lead import LeadCreate, LeadOut, LeadUpdate
from bot.services.sheets_service import (
    list_leads as list_leads_service,
    save_lead,
    update_lead_by_id,
    DuplicateLeadError,
    LeadNotFoundError,
    DuplicatePhoneError,
)

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/leads", status_code=201, response_model=LeadOut)
def create_lead(payload: LeadCreate):
    try:
        return save_lead(payload)
    except DuplicateLeadError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/leads")
def list_leads():
    return list_leads_service()


@router.patch("/leads/{lead_id}", response_model=LeadOut)
def patch_lead(lead_id: str, payload: LeadUpdate):
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        updated = update_lead_by_id(lead_id, updates)
        return updated
    except LeadNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicatePhoneError as e:
        raise HTTPException(status_code=409, detail=str(e))