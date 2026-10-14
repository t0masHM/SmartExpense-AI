from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, Token, UserCreate, UserOut

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email.lower()).first()
    if exists:
        raise HTTPException(400, "Ese correo ya está registrado")
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        company_name=payload.company_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Credenciales inválidas")
    return Token(access_token=create_access_token(user.email))


@router.post("/token", response_model=Token)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Credenciales inválidas")
    return Token(access_token=create_access_token(user.email))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
