from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Receipt
from app.services.char_model import ensure_model
from app.services.ocr import run_ocr
from app.services.parser import parse_chilean_receipt
from app.services.reconstruction import restore_image

ALLOWED = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def _user_dir(user_id: int) -> Path:
    path = Path(get_settings().upload_dir) / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(user_id: int, filename: str, data: bytes) -> Path:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError("Formato no soportado. Use JPG, PNG, WEBP o TIFF.")
    dest = _user_dir(user_id) / f"{uuid4().hex}{ext}"
    dest.write_bytes(data)
    return dest


def process_receipt(db: Session, receipt: Receipt) -> Receipt:
    receipt.status = "processing"
    db.commit()
    try:
        ensure_model()
        payload = Path(receipt.stored_path).read_bytes()
        image = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("No se pudo leer la imagen")

        restoration = restore_image(image)
        stem = Path(receipt.stored_path).stem
        folder = Path(receipt.stored_path).parent
        restored_path = folder / f"{stem}_restored.png"
        mask_path = folder / f"{stem}_mask.png"
        cv2.imwrite(str(restored_path), restoration.restored)
        cv2.imwrite(str(mask_path), restoration.mask)

        ocr = run_ocr(restoration.restored)
        parsed = parse_chilean_receipt(ocr.text)

        notes = list(restoration.notes)
        notes.extend(parsed.get("parse_notes") or [])
        if ocr.reconstructed_chars:
            notes.append(f"{ocr.reconstructed_chars} caracteres reconstruidos por el modelo HOG+RF")

        receipt.restored_path = str(restored_path)
        receipt.mask_path = str(mask_path)
        receipt.raw_text = ocr.text
        receipt.confidence = ocr.mean_confidence
        receipt.damage_score = restoration.damage_score
        receipt.document_type = parsed.get("document_type")
        receipt.merchant = parsed.get("merchant")
        receipt.rut_emisor = parsed.get("rut_emisor")
        receipt.rut_receptor = parsed.get("rut_receptor")
        receipt.folio = parsed.get("folio")
        receipt.issued_at = parsed.get("issued_at")
        receipt.net_amount = parsed.get("net_amount")
        receipt.tax_amount = parsed.get("tax_amount")
        receipt.total_amount = parsed.get("total_amount")
        receipt.reconstruction_notes = " · ".join(notes) if notes else None
        receipt.extracted_json = {
            "ocr_confidence": ocr.mean_confidence,
            "reconstructed_chars": ocr.reconstructed_chars,
            "damage_score": restoration.damage_score,
            "boxes": ocr.boxes[:80],
            **parsed,
        }
        receipt.status = "done"
        receipt.error_message = None
        receipt.processed_at = datetime.utcnow()
    except Exception as exc:  # noqa: BLE001
        receipt.status = "failed"
        receipt.error_message = str(exc)
        receipt.processed_at = datetime.utcnow()
    db.commit()
    db.refresh(receipt)
    return receipt
