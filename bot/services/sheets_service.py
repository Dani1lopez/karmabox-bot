# bot/services/sheets_service.py

import os
from functools import lru_cache
from uuid import uuid4
from datetime import datetime, timezone
import gspread

from bot.schemas.lead import LeadCreate, LeadOut
from bot.utils.phone import normalize_phone
from bot.utils.lead_mapper import normalize_lead_record

SHEET_NAME = os.getenv("SHEET_NAME", "KarmaBox Leads")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "secrets/service_account.json")

@lru_cache
def _get_ws():
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    sh = gc.open(SHEET_NAME)
    return sh.sheet1


class DuplicateLeadError(Exception):
    pass

class LeadNotFoundError(Exception):
    pass


class DuplicatePhoneError(Exception):
    pass


def list_leads() -> list[dict]:
    records = _get_ws().get_all_records()
    out: list[dict] = []
    
    for r in records:
        nr = normalize_lead_record(r)
        if not nr["id"]:
            continue
        out.append(nr)
    return out


def save_lead(payload: LeadCreate) -> LeadOut:
    rows = _get_ws().get_all_records()
    if any(normalize_phone(r.get("phone", "")) == payload.phone for r in rows):
        raise DuplicateLeadError("Ya existe un lead con ese teléfono.")

    lead = LeadOut(
        id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        **payload.model_dump(),
    )

    _get_ws().append_row([
        lead.id,
        lead.created_at,
        lead.name,
        lead.last_name,
        lead.phone,
        lead.address,
    ])
    return lead


def update_lead_by_id(lead_id: str, updates: dict) -> dict:
    """
    Actualiza un lead por su 'id' en Google Sheets.
    - updates: dict con campos (name, last_name, phone, address)
    - Valida duplicado de phone si se actualiza
    - Devuelve el lead actualizado como dict
    """
    values = _get_ws().get_all_values()
    if not values or len(values) < 2:
        raise LeadNotFoundError("No hay datos")
    
    headers = values[0]
    try:
        id_col = headers.index("id")
        phone_col = headers.index("phone")
    except ValueError:
        raise RuntimeError("Headers inválidos: faltan columnas 'id' o 'phone'")
    
    #localizar la fila real
    target_row = None
    for row_idx, row in enumerate(values[1:], start=2):
        if len(row) > id_col and row[id_col] == lead_id:
            target_row = row_idx
            break
    
    if target_row is None:
        raise LeadNotFoundError("Lead no encontrado")
    
    # Si se actualiza phone: normalizar + comprobar duplicado excluyendo el propio lead
    if "phone" in updates and updates["phone"] is not None:
        new_phone = normalize_phone(str(updates["phone"]))
        for row_idx, row in enumerate(values[1:], start=2):
            if row_idx == target_row:
                continue
            existing_raw = row[phone_col] if len(row) > phone_col else ""
            if existing_raw and normalize_phone(existing_raw) == new_phone:
                raise DuplicatePhoneError("Ya existe un lead con ese teléfono.")
        updates["phone"] = new_phone
    allowed = {"name", "last_name", "phone", "address"}
    
    
    #actualizar celdas
    for field, value in updates.items():
        if field not in allowed:
            continue
        if value is None:
            continue
        if field not in headers:
            continue
        
        col_idx = headers.index(field) + 1 #gspread es 1-based
        _get_ws().update_cell(target_row, col_idx, str(value))
    #devolver fila actualizada como dict
    updated_row = _get_ws().row_values(target_row)
    raw = {headers[i]: (updated_row[i] if i < len(updated_row) else "") for i in range(len(headers))}
    return normalize_lead_record(raw)