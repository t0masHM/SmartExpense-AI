from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routers import auth, receipts, reports
from app.services.char_model import ensure_model

settings = get_settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.model_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="CAPTON",
    description="Digitalización, extracción y reconstrucción on-premise de comprobantes.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(receipts.router)
app.include_router(reports.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_model()


@app.get("/health")
def health():
    return {"status": "ok", "service": "capton-api"}
