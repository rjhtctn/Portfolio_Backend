# routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi.responses import JSONResponse
import secrets
from datetime import timedelta

from core.database import get_db
from core.security import (
    hash_password, verify_password, create_token, decode_token
)
from schemas.user_schema import UserCreate, UserLogin, UserResponse
from models.user import User
from helpers.email_sender import send_email_async
from core.config import FRONTEND_URL
from core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_user_by_username_or_email(db: Session, identifier: str) -> User | None:
    """Kullanıcıyı kullanıcı adı veya e-postaya göre case-insensitive (büyük/küçük harf duyarsız) arar."""
    # Bu, SQLAlchemy için en doğru ve performanslı sorgudur.
    # IDE'nin yanlış "InstrumentedAttribute" uyarısını susturmak için # noqa ekliyoruz.
    return db.query(User).filter(
        or_(
            User.username.ilike(identifier),
            User.email.ilike(identifier)
        )  # noqa
    ).first()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_data: UserCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    existing_user = get_user_by_username_or_email(db, user_data.username) or \
                    get_user_by_username_or_email(db, str(user_data.email))

    if existing_user:
        raise HTTPException(status_code=400, detail="Email veya kullanıcı adı zaten kayıtlı.")

    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        email=str(user_data.email),
        password=hash_password(user_data.password)
    )

    evt = secrets.token_hex(16)
    new_user.email_verify_token = evt
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token_payload = {"user_id": new_user.id, "evt": evt}
    token = create_token(token_payload, token_type="email_verify")
    verify_link = f"{FRONTEND_URL}/verify-email?token={token}"

    subject = "PortfolioApp - E-posta Doğrulama"
    body = f"Merhaba {new_user.first_name},\n\nHesabınızı aktif hale getirmek için linke tıklayın:\n{verify_link}"
    background_tasks.add_task(send_email_async, new_user.email, subject, body)

    return new_user


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token, expected_type="email_verify")
    user = db.query(User).filter_by(id=payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if user.is_verified:
        return {"message": "E-posta zaten doğrulanmış."}

    token_evt = payload.get("evt")
    if not token_evt or not user.email_verify_token or token_evt != user.email_verify_token:
        raise HTTPException(status_code=400, detail="Bu doğrulama bağlantısı artık geçersiz.")

    user.is_verified = True
    user.email_verify_token = None
    db.commit()
    return {"message": "E-posta başarıyla doğrulandı. Artık giriş yapabilirsiniz."}


@router.post("/login")
async def login_user(credentials: UserLogin, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = get_user_by_username_or_email(db, credentials.username_or_email)
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı.")

    if not user.is_verified:
        evt = secrets.token_hex(16)
        user.email_verify_token = evt
        db.commit()

        token_payload = {"user_id": user.id, "evt": evt}
        token = create_token(token_payload, token_type="email_verify")
        verify_link = f"{FRONTEND_URL}/verify-email?token={token}"
        subject = "PortfolioApp - E-posta Doğrulama (Yeniden Gönderim)"
        body = f"Merhaba {user.first_name},\n\nHesabınızı aktif hale getirmek için linke tıklayın:\n{verify_link}"
        background_tasks.add_task(send_email_async, user.email, subject, body)
        return JSONResponse(
            status_code=403,
            content={"detail": "E-posta doğrulanmamış. Yeni bir doğrulama maili gönderildi."}
        )

    token_payload = {"user_id": user.id, "email": user.email, "username": user.username}
    access_token = create_token(token_payload, token_type="access")

    return {
        "access_token": access_token, "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email, "is_admin": user.is_admin}
    }


@router.post("/forgot-password")
async def forgot_password(
        background_tasks: BackgroundTasks,
        email: str = Query(..., description="Şifre sıfırlama linkinin gönderileceği e-posta"),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email.ilike(email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Bu e-posta ile kayıtlı kullanıcı bulunamadı.")

    token_payload = {"user_id": user.id}
    token = create_token(token_payload, token_type="password_reset", expires_delta=timedelta(hours=1))
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    subject = "PortfolioApp - Şifre Sıfırlama"
    body = f"Merhaba {user.first_name},\n\nŞifrenizi sıfırlamak için linke tıklayın:\n{reset_link}"
    background_tasks.add_task(send_email_async, str(user.email), subject, body)
    return {"message": "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi."}


@router.post("/reset-password")
async def reset_password(
        token: str = Query(..., description="Şifre sıfırlama token’ı"),
        new_password: str = Query(..., description="Yeni şifre"),
        db: Session = Depends(get_db)
):
    payload = decode_token(token, expected_type="password_reset")
    user = db.query(User).filter_by(id=payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    user.password = hash_password(new_password)
    db.commit()

    subject = "PortfolioApp - Şifreniz Güncellendi"
    body = f"Merhaba {user.first_name},\n\nŞifreniz başarıyla güncellendi."
    await send_email_async(str(user.email), subject, body)
    return {"message": "Şifreniz başarıyla güncellendi."}


@router.post("/change-password")
async def change_password(
        current_password: str = Query(..., description="Mevcut şifre"),
        new_password: str = Query(..., description="Yeni şifre"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if not verify_password(current_password, current_user.password):
        raise HTTPException(status_code=401, detail="Mevcut şifre hatalı.")
    if verify_password(new_password, current_user.password):
        raise HTTPException(status_code=400, detail="Yeni şifre mevcut şifreyle aynı olamaz.")

    current_user.password = hash_password(new_password)
    db.commit()

    subject = "PortfolioApp - Şifreniz Değiştirildi"
    body = f"Merhaba {current_user.first_name},\n\nŞifreniz başarıyla değiştirildi."
    await send_email_async(current_user.email, subject, body)
    return {"message": "Şifreniz başarıyla güncellendi."}