from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Receipt, User
from app.schemas import DashboardStats, ReceiptDetail, ReceiptOut
from app.services.pipeline import process_receipt, save_upload
from app.services.sample import render_demo_boleta
from sqlalchemy import func

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.get("", response_model=list[ReceiptOut])
def list_receipts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    q: str | None = None,
    status: str | None = None,
):
    query = db.query(Receipt).filter(Receipt.owner_id == user.id)
    if status:
        query = query.filter(Receipt.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Receipt.merchant.ilike(like))
            | (Receipt.rut_emisor.ilike(like))
            | (Receipt.original_filename.ilike(like))
            | (Receipt.folio.ilike(like))
        )
    return query.order_by(Receipt.created_at.desc()).all()


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    base = db.query(Receipt).filter(Receipt.owner_id == user.id)
    total = base.count()
    processed = base.filter(Receipt.status == "done").count()
    failed = base.filter(Receipt.status == "failed").count()
    reconstructed = (
        base.filter(Receipt.reconstruction_notes.isnot(None)).filter(Receipt.status == "done").count()
    )
    total_amount = (
        db.query(func.coalesce(func.sum(Receipt.total_amount), 0))
        .filter(Receipt.owner_id == user.id)
        .scalar()
    )
    avg_conf = (
        db.query(func.avg(Receipt.confidence))
        .filter(Receipt.owner_id == user.id, Receipt.confidence.isnot(None))
        .scalar()
    )
    avg_dmg = (
        db.query(func.avg(Receipt.damage_score))
        .filter(Receipt.owner_id == user.id, Receipt.damage_score.isnot(None))
        .scalar()
    )
    return DashboardStats(
        total_receipts=total,
        processed=processed,
        failed=failed,
        reconstructed=reconstructed,
        total_amount=float(total_amount or 0),
        avg_confidence=float(avg_conf or 0),
        avg_damage=float(avg_dmg or 0),
    )


@router.post("/upload", response_model=ReceiptOut)
async def upload_receipt(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, "Archivo vacío")
    if len(data) > 12 * 1024 * 1024:
        raise HTTPException(400, "El archivo supera 12 MB")
    try:
        path = save_upload(user.id, file.filename or "comprobante.jpg", data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    receipt = Receipt(
        owner_id=user.id,
        original_filename=file.filename or path.name,
        stored_path=str(path),
        status="pending",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    background.add_task(_run_pipeline, receipt.id)
    return receipt


@router.post("/demo", response_model=ReceiptOut)
def upload_demo(
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = render_demo_boleta()
    path = save_upload(user.id, "boleta_demo_capton.png", data)
    receipt = Receipt(
        owner_id=user.id,
        original_filename="boleta_demo_capton.png",
        stored_path=str(path),
        status="pending",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    background.add_task(_run_pipeline, receipt.id)
    return receipt


def _run_pipeline(receipt_id: int) -> None:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        rec = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if rec:
            process_receipt(db, rec)
    finally:
        db.close()


@router.post("/{receipt_id}/reprocess", response_model=ReceiptOut)
def reprocess(receipt_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.owner_id == user.id).first()
    if not rec:
        raise HTTPException(404, "Comprobante no encontrado")
    return process_receipt(db, rec)


@router.get("/{receipt_id}", response_model=ReceiptDetail)
def get_receipt(receipt_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.owner_id == user.id).first()
    if not rec:
        raise HTTPException(404, "Comprobante no encontrado")
    data = ReceiptDetail.model_validate(rec)
    data.has_restored = bool(rec.restored_path)
    data.has_mask = bool(rec.mask_path)
    return data


@router.get("/{receipt_id}/image")
def receipt_image(
    receipt_id: int,
    kind: str = "original",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rec = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.owner_id == user.id).first()
    if not rec:
        raise HTTPException(404, "Comprobante no encontrado")
    mapping = {
        "original": rec.stored_path,
        "restored": rec.restored_path,
        "mask": rec.mask_path,
    }
    path = mapping.get(kind)
    if not path:
        raise HTTPException(404, "Imagen no disponible")
    return FileResponse(path)


@router.delete("/{receipt_id}")
def delete_receipt(receipt_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rec = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.owner_id == user.id).first()
    if not rec:
        raise HTTPException(404, "Comprobante no encontrado")
    db.delete(rec)
    db.commit()
    return {"ok": True}
