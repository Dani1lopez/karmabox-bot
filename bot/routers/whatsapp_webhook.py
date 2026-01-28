import os
import json
import logging
import hmac
import hashlib
import inspect
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

from bot.services.conversation_flow import handle_message
from bot.services.sheets_service import was_message_processed, mark_message_processed

logger = logging.getLogger("whatsapp")

router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp"])


# -----------------------------
# Config
# -----------------------------
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_GRAPH_VERSION = os.getenv("WHATSAPP_GRAPH_VERSION", "v19.0")


# -----------------------------
# Helpers
# -----------------------------
def verify_signature_if_configured(raw_body: bytes, signature_header: Optional[str]) -> None:
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
    out: List[Dict[str, Any]] = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value") or {}
            for msg in (value.get("messages") or []):
                out.append(msg)
    return out


def extract_user_text(msg: Dict[str, Any]) -> Tuple[Optional[str], str]:
    """
    Devuelve (texto, tipo_detectado)
    Soporta: text, interactive (list/button), legacy button
    """
    mtype = msg.get("type") or ""

    if mtype == "text":
        return ((msg.get("text") or {}).get("body"), "text")

    if mtype == "interactive":
        inter = msg.get("interactive") or {}
        itype = inter.get("type") or ""
        if itype == "button_reply":
            br = inter.get("button_reply") or {}
            return (br.get("title") or br.get("id"), "interactive.button_reply")
        if itype == "list_reply":
            lr = inter.get("list_reply") or {}
            return (lr.get("title") or lr.get("id"), "interactive.list_reply")
        return (None, f"interactive.{itype or 'unknown'}")

    if mtype == "button":  # legacy
        btn = msg.get("button") or {}
        return (btn.get("text") or btn.get("payload"), "button.legacy")

    return (None, mtype or "unknown")


async def send_whatsapp_text(to_wa_id: str, text: str) -> None:
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WHATSAPP: faltan credenciales (no se envía nada).")
        return

    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
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


async def mark_whatsapp_read(message_id: str) -> None:
    if not message_id or not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        return

    url = f"https://graph.facebook.com/{WHATSAPP_GRAPH_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, headers=headers, json=data)


async def run_handle_message(sender_id: str, text: str) -> Optional[str]:
    res: Any = handle_message(sender_id, text)  # str o coroutine
    if inspect.isawaitable(res):
        res = await res
    if res is None:
        return None
    reply = str(res).strip()
    return reply or None


# -----------------------------
# Routes
# -----------------------------
@router.get("")
def verify_whatsapp_webhook(request: Request):
    qp = request.query_params
    mode = qp.get("hub.mode")
    token = qp.get("hub.verify_token")
    challenge = qp.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN and challenge:
        return PlainTextResponse(content=challenge, status_code=200)

    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("")
async def whatsapp_webhook(request: Request):
    raw = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    verify_signature_if_configured(raw, signature)

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    messages = extract_messages(payload)
    if not messages:
        return JSONResponse({"ok": True, "detail": "no messages"}, status_code=200)

    for msg in messages:
        wa_from = msg.get("from")
        msg_id = msg.get("id")  # wamid...

        if not wa_from:
            continue

        # Idempotencia persistente
        if msg_id and was_message_processed(msg_id):
            logger.info("WA duplicated message ignored: %s", msg_id)
            continue
        if msg_id:
            mark_message_processed(msg_id)

        # Mark as read (nice)
        if msg_id:
            await mark_whatsapp_read(msg_id)

        user_text, detected = extract_user_text(msg)
        if not user_text:
            await send_whatsapp_text(
                wa_from,
                "Ahora mismo solo entiendo texto (y botones/listas). Escríbeme tu consulta o pon 'start'."
            )
            logger.info("WA non-text handled (%s). from=%s id=%s", detected, wa_from, msg_id)
            continue

        reply = await run_handle_message(wa_from, user_text)
        if reply:
            await send_whatsapp_text(wa_from, reply)

    return JSONResponse({"ok": True}, status_code=200)