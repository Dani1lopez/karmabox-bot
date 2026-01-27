# bot/schemas/lead.py

from pydantic import BaseModel, field_validator
from typing import Optional
from bot.utils.phone import normalize_phone, validate_phone_es


class LeadCreate(BaseModel):
    name: str
    last_name: str
    phone: str
    address: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return validate_phone_es(v)


class LeadOut(LeadCreate):
    id: str
    created_at: str


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_phone_es(v)


