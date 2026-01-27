# bot/services/sheets_service.py

from uuid import uuid4
from datetime import datetime, timezone
import gspread

from bot.schemas.lead import LeadCreate, LeadOut
from bot.utils.phone import normalize_phone


SHEET_NAME = "KarmaBox Leads"
SERVICE_ACCOUNT_FILE = "secrets/service_account.json"

# Conectamos una vez al arrancar/importar el módulo (simple para demo)
gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
sh = gc.open(SHEET_NAME)
ws = sh.sheet1


class DuplicateLeadError(Exception):
    pass


def list_leads() -> list[dict]:
    return ws.get_all_records()


def save_lead(payload: LeadCreate) -> LeadOut:
    rows = ws.get_all_records()
    if any(normalize_phone(r.get("phone", "")) == payload.phone for r in rows):
        raise DuplicateLeadError("Ya existe un lead con ese teléfono.")

    lead = LeadOut(
        id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        **payload.model_dump(),
    )

    ws.append_row([
        lead.id,
        lead.created_at,
        lead.name,
        lead.last_name,
        lead.phone,
        lead.address,
    ])

    return lead