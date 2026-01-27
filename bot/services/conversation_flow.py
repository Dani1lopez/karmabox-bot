from dataclasses import dataclass, field
from typing import Literal

from bot.schemas.lead import LeadCreate
from bot.services.sheets_service import save_lead, DuplicateLeadError
from bot.utils.phone import validate_phone_es
from bot.services.ai_client import ai_reply

Step = Literal["name","last_name","phone","address","confirm"]

@dataclass
class Session:
    step: Step = "name"
    data: dict = field(default_factory=dict)

#Memoria en ram para demo

_sessions: dict[str, Session] = {}

def has_session(user_id: str) -> bool:
    return user_id in _sessions

def clear_session(user_id: str) -> None:
    _sessions.pop(user_id, None)

def reset_session(user_id: str) -> Session:
    s = Session()
    _sessions[user_id] = s
    return s

def get_session(user_id: str) -> Session:
    return _sessions.get(user_id) or reset_session(user_id)


def handle_message(user_id: str, text: str) -> str:
    text = (text or "").strip()
    
    #Comandos
    if text.lower() in {"/start", "start"}:
        reset_session(user_id)
        return "¡Vamos! 👇\nDime tu *nombre*."
    
    if text.lower() in {"/cancel", "cancel"}:
        clear_session(user_id)
        return "Cancelado ✅. Si quieres empezar otra vez: /start"
    
    #Si no hay session entonces IA
    if not has_session(user_id):
        return ai_reply(text)
    
    s = get_session(user_id)
    
    #Flujo
    if s.step == "name":
        if len(text) < 2:
            return "Nombre demasiado corto. Dime tu *nombre* (mín. 2 letras)."
        s.data["name"] = text
        s.step = "last_name"
        return "Perfecto. Ahora dime tus *apellidos*."
    
    if s.step == "last_name":
        if len(text) < 2:
            return "Apellidos demasiado cortos. Dime tus *apellidos*."
        s.data["last_name"] = text
        s.step = "phone"
        return "Genial. Ahora dime tu *teléfono* (España, 9 dígitos). Ej: 654789098"
    
    if s.step == "phone":
        try:
            s.data["phone"] = validate_phone_es(text)
        except ValueError as e:
            return f"{e}\nPrueba otra vez. Ej: 654789098"
        s.step = "address"
        return "Bien. Ahora dime tu *dirección*."
    
    if s.step == "address":
        if len(text) < 5:
            return "Dirección muy corta. Dime una dirección más completa."
        s.data["address"] = text
        s.step = "confirm"
        return (
            "Confirma por favor:\n"
            f"• Nombre: {s.data['name']}\n"
            f"• Apellidos: {s.data['last_name']}\n"
            f"• Teléfono: {s.data['phone']}\n"
            f"• Dirección: {s.data['address']}\n\n"
            "Responde: *sí* / *no*"
        )
    
    if s.step == "confirm":
        t = text.lower()
        if t in {"si","sí","s","yes","y"}:
            try:
                payload = LeadCreate(**s.data)
                lead = save_lead(payload)
                reset_session(user_id)
                return f"✅ Guardado correctamente. ID: {lead.id}"
            except DuplicateLeadError:
                reset_session(user_id)
                return "⚠️ Ese teléfono ya existe en la sheet. Si quieres probar con otro: /start"
            except Exception:
                # Evita explotar en demo; en prod loguearías.
                reset_session(user_id)
                return "❌ Ha ocurrido un error guardando el lead. Intenta de nuevo con /start"
        
        if t in {"no","n"}:
            reset_session(user_id)
            return "Vale, no guardo nada ✅. Si quieres empezar otra vez: /start"
        
        return "No te he entendido. Responde *sí* o *no*."
    #fallback
    reset_session(user_id)
    return "Vamos a reiniciar. Escribe /start"