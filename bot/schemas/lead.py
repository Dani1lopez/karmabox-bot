# bot/schemas/lead.py

from pydantic import BaseModel, field_validator
from bot.utils.phone import validate_phone_es


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