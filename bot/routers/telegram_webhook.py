import os
import httpx
from fastapi import APIRouter, Request

from bot.services.conversation_flow import handle_message

router = APIRouter()



@router.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    update = await request.json()
    
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text")
    
    #Si no es mensaje de texto, respondemos OK y ya esta
    if not chat_id or not text:
        return {"ok": True}
    
    reply = handle_message(str(chat_id), text)
    
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not telegram_token:
        print("ERROR: TELEGRAM_BOT_TOKEN vacío")
        return {"ok": True}
    #Responder por Telgram API
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, json={"chat_id": chat_id, "text": reply})
    
    return {"ok": True}