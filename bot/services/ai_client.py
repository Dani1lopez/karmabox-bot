import os
import httpx
from typing import Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


async def ai_reply(user_text: str, history: Optional[list[dict]] = None) -> str:
    """
    Llama a Groq para generar una respuesta (ASYNC).
    """
    if not GROQ_API_KEY:
        return "Ahora mismo no tengo IA configurada (falta GROQ_API_KEY)."

    messages = [
        {
            "role": "system",
            "content": (
                "Eres un asistente de KarmaBox. Responde breve y claro. "
                "Si el usuario quiere registrarse o dejar sus datos, dile que escriba 'start' (o /start) "
                "para iniciar el formulario. "
                "Si pregunta dudas (horario, servicios, precios, ubicación), contesta de forma útil."
            ),
        }
    ]

    if history:
        messages.extend(history[-8:])

    messages.append({"role": "user", "content": user_text})

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                GROQ_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": AI_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 250,
                },
            )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return "Perdona, ahora mismo estoy teniendo un problema con la IA. ¿Quieres iniciar el formulario con 'start'?"