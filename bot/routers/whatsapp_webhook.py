import os
import json
import logging
import hmac
import hashlib
import inspect
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from bot.services.conversation_flow import handle_message

logger = logging.getLogger("whatsapp")

router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


# -----------------------------
# Config
# -----------------------------
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

# Opcional pero recomendado (firma de Meta en POST)
# Header: X-Hub-Signature-256: sha256=<hex>
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")


# -----------------------------
# Helpers
# -----------------------------
def verify_signature_if_configured(raw_body: bytes, signature_header: Optional[str]) -> None:
    """
    Si WHATSAPP_APP_SECRET está definido, valida la firma X-Hub-Signature-256.
    Si no, no hace nada 
    """
    if not WHATSAPP_APP_SECRET:
        return

    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing/invalid X-Hub-Signature-256")

    expected = hmac.new(
        WHATSAPP_APP_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    received = signature_header.split("sha256=", 1)[1].strip()
    if not hmac.compare_digest(received, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")


def extract_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Aplana entry -> changes -> value -> messages (si existen).
    Si llegan eventos de 'statuses' u otros, devuelve lista vacía y respondemos 200.
    """
    out: List[Dict[str, Any]] = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            messages = value.get("messages") or []
            for msg in messages:
                out.append(msg)
    return out


def extract_text(msg: Dict[str, Any]) -> Optional[str]:
    """
    Por ahora solo texto
    """
    if msg.get("type") != "text":
        return None
    return (msg.get("text") or {}).get("body")


async def send_whatsapp_text(to_wa_id: str, text: str) -> None:
    """
    Envía un mensaje usando Cloud API. Si faltan tokens/phone_number_id, no falla.
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WHATSAPP: faltan WHATSAPP_ACCESS_TOKEN o WHATSAPP_PHONE_NUMBER_ID (no se envía nada).")
        return

    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, headers=headers, json=data)

    if r.status_code >= 400:
        logger.warning("WA send failed: %s %s", r.status_code, r.text)
    else:
        logger.info("WA send ok: %s", r.status_code)


async def run_handle_message(wa_from: str, text: str) -> Optional[str]:
    """
    Ejecuta tu core handler. Soporta que sea sync o async.
    Esperamos que devuelva un 'reply' (str) o None.
    """
    result = handle_message(wa_from, text)
    if inspect.isawaitable(result):
        result = await result
    if result is None:
        return None
    return str(result).strip() or None


# -----------------------------
# Routes
# -----------------------------


@router.get("")
def verify_whatsapp_webhook(request: Request):
    qp = request.query_params

    mode = qp.get("hub.mode")
    token = qp.get("hub.verify_token")
    challenge = qp.get("hub.challenge")

    expected = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

    
    logger.debug(
        "WA verify: mode=%s token_ok=%s challenge_present=%s",
        mode,
        token == expected,
        bool(challenge),
    )   

    if mode == "subscribe" and token == expected and challenge:
        return PlainTextResponse(content=challenge, status_code=200)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("")
async def whatsapp_webhook(request: Request):
    """
    Webhook events:
    - (Opcional) verifica firma si WHATSAPP_APP_SECRET está configurado
    - parsea JSON
    - extrae mensajes
    - llama a tu core handler
    - intenta responder por WhatsApp si tiene credenciales
    """
    raw = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    verify_signature_if_configured(raw, signature)

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    messages = extract_messages(payload)
    if not messages:
        # statuses u otros eventos: respondemos ok igualmente
        return JSONResponse({"ok": True, "detail": "no messages"}, status_code=200)

    for msg in messages:
        wa_from = msg.get("from")
        if not wa_from:
            continue

        text = extract_text(msg)
        if not text:
            continue

        reply = await run_handle_message(wa_from, text)
        if reply:
            await send_whatsapp_text(wa_from, reply)

    return JSONResponse({"ok": True}, status_code=200)