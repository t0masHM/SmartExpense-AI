from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Receipt, User
from app.services.excel_export import receipts_to_excel

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/excel")
def excel_report(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    receipts = (
        db.query(Receipt)
        .filter(Receipt.owner_id == user.id)
        .order_by(Receipt.created_at.desc())
        .all()
    )
    payload = receipts_to_excel(user, receipts)
    filename = "capton_reporte_contable.xlsx"
    return StreamingResponse(
        iter([payload]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
