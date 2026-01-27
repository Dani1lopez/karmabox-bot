# bot/routers/leads.py

from fastapi import APIRouter, HTTPException
from bot.schemas.lead import LeadCreate, LeadOut
from bot.services.sheets_service import list_leads as list_leads_service, save_lead, DuplicateLeadError

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

@router.get("/leads", response_model=list[LeadOut])
def list_leads():
    return list_leads_service()