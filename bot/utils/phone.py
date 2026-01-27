def normalize_phone(v) -> str:
    s = str(v or "").strip().replace(" ", "").replace("-", "").replace(".", "")
    if s.startswith("+34"):
        s = s[3:]
    elif s.startswith("34") and len(s) == 11:
        s = s[2:]
    return s

def validate_phone_es(v: str) -> str:
    cleaned = normalize_phone(v)
    if len(cleaned) != 9 or not cleaned.isdigit():
        raise ValueError("Teléfono inválido: debe tener 9 dígitos (España). Ej: 654789098")
    if cleaned[0] not in {"6", "7", "8", "9"}:
        raise ValueError("Teléfono inválido: debe empezar por 6, 7, 8 o 9 (España).")
    return cleaned






