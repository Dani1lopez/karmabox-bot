import os
import inspect
import httpx
from fastapi import APIRouter, Request
from typing import Optional, Any

from bot.services.conversation_flow import handle_message

router = APIRouter()


async def run_handle_message(sender_id: str, text: str, source: str) -> Optional[str]:
    res: Any = handle_message(sender_id, text, source=source)
    if inspect.isawaitable(res):
        res = await res
    if res is None:
        return None
    reply = str(res).strip()
    return reply or None


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    update = await request.json()

    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text")

    if not chat_id or not text:
        return {"ok": True}

    reply = await run_handle_message(str(chat_id), text, source="telegram")

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not telegram_token:
        print("ERROR: TELEGRAM_BOT_TOKEN vacío")
        return {"ok": True}

    if not reply:
        return {"ok": True}

    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={"chat_id": chat_id, "text": reply})

    return {"ok": True}