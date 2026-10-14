from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str] = mapped_column(String(255), default="Empresa local")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    receipts: Mapped[list["Receipt"]] = relationship(back_populates="owner")


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    stored_path: Mapped[str] = mapped_column(String(1024))
    restored_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    mask_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rut_emisor: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rut_receptor: Mapped[str | None] = mapped_column(String(32), nullable=True)
    folio: Mapped[str | None] = mapped_column(String(64), nullable=True)
    issued_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    net_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    tax_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    damage_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reconstruction_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="receipts")
