# bot/utils/lead_mapper.py

from typing import Any, Dict
from bot.utils.phone import normalize_phone


def normalize_lead_record(r: Dict[str, Any]) -> Dict[str, str]:
    """
    Normaliza un registro de lead que viene de Google Sheets (gspread).
    - Acepta posibles typos en headers (crated_at)
    - Fuerza strings
    - Normaliza phone (si existe)
    """
    created = r.get("created_at") or r.get("crated_at") or ""

    phone_raw = r.get("phone", "")
    phone_str = str(phone_raw).strip()
    phone_norm = normalize_phone(phone_str) if phone_str else ""

    return {
        "id": str(r.get("id", "")).strip(),
        "created_at": str(created).strip(),
        "name": str(r.get("name", "")).strip(),
        "last_name": str(r.get("last_name", "")).strip(),
        "phone": phone_norm,
        "address": str(r.get("address", "")).strip(),
    }