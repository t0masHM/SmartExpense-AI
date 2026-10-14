from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    company_name: str = "Empresa local"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    company_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ReceiptOut(BaseModel):
    id: int
    original_filename: str
    status: str
    document_type: str | None
    merchant: str | None
    rut_emisor: str | None
    rut_receptor: str | None
    folio: str | None
    issued_at: str | None
    net_amount: float | None
    tax_amount: float | None
    total_amount: float | None
    confidence: float | None
    damage_score: float | None
    reconstruction_notes: str | None
    extracted_json: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class ReceiptDetail(ReceiptOut):
    raw_text: str | None
    has_restored: bool = False
    has_mask: bool = False


class DashboardStats(BaseModel):
    total_receipts: int
    processed: int
    failed: int
    reconstructed: int
    total_amount: float
    avg_confidence: float
    avg_damage: float
