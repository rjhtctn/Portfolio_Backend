from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from sqlalchemy import or_
import secrets

from core.database import get_db
from core.security import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
    create_email_verify_token,   # ✅ yeni
)
from schemas.user_schema import UserCreate, UserLogin, UserResponse
from models.user import User
from helpers.email_sender import send_email_async
from core.config import FRONTEND_URL
from core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        or_(User.email == str(user_data.email), User.username == str(user_data.username))
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email veya kullanıcı adı zaten kayıtlı.")

    hashed_pw = hash_password(user_data.password)

    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        email=user_data.email,
        password=hashed_pw,
        is_verified=False,
        is_admin=False
    )

    # ✅ ilk doğrulama için tek-kullanımlık nonce üret
    evt = secrets.token_hex(32)  # 64 hex karakter
    new_user.email_verify_token = evt

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_email_verify_token(new_user, evt)
    verify_link = f"{FRONTEND_URL}/verify-email?token={token}"

    subject = "PortfolioApp - E-posta Doğrulama"
    body = (
        f"Merhaba {new_user.first_name},\n\n"
        f"Hesabınızı aktif hale getirmek için aşağıdaki bağlantıya tıklayın:\n"
        f"{verify_link}\n\n"
        "Teşekkürler!\nPortfolioApp"
    )

    background_tasks.add_task(send_email_async, new_user.email, subject, body)

    return new_user

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş bağlantı.")

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    if user.is_verified:
        return {"message": "E-posta zaten doğrulanmış."}

    # ✅ tek-kullanımlık bağlantı kontrolü (nonce eşleşmeli)
    token_evt = payload.get("evt")
    if not token_evt or not user.email_verify_token or token_evt != user.email_verify_token:
        raise HTTPException(status_code=400, detail="Bu doğrulama bağlantısı artık geçersiz.")

    user.is_verified = True
    user.email_verify_token = None
    db.commit()

    return {"message": "E-posta başarıyla doğrulandı. Artık giriş yapabilirsiniz."}

@router.post("/login")
async def login_user(
    credentials: UserLogin,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        or_(User.username == credentials.username_or_email, User.email == credentials.username_or_email)
    ).first()

    if not user:
        raise HTTPException(status_code=400, detail="Kullanıcı bulunamadı.")

    if not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Geçersiz şifre.")

    if not user.is_verified:
        # ✅ yeniden doğrulama: nonce yenile → eskiler geçersiz
        evt = secrets.token_hex(32)
        user.email_verify_token = evt
        db.commit()

        token = create_email_verify_token(user, evt)
        verify_link = f"{FRONTEND_URL}/verify-email?token={token}"

        subject = "PortfolioApp - E-posta Doğrulama (Yeniden Gönderim)"
        body = (
            f"Merhaba {user.first_name},\n\n"
            f"Hesabınızı aktif hale getirmek için aşağıdaki bağlantıya tıklayın:\n"
            f"{verify_link}\n\n"
            "Teşekkürler!\nPortfolioApp"
        )

        background_tasks.add_task(send_email_async, user.email, subject, body)
        return JSONResponse(
            status_code=403,
            content={"detail": "E-posta doğrulanmamış. Yeni bir doğrulama maili gönderildi."}
        )

    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }

@router.post("/forgot-password")
async def forgot_password(
    background_tasks: BackgroundTasks,
    email: str = Query(..., description="Şifre sıfırlama bağlantısının gönderileceği e-posta adresi"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Bu e-posta ile kayıtlı kullanıcı bulunamadı.")

    # Şimdilik reset akışı eski gibi kalsın (istersen buna da nonce ekleriz)
    token = create_access_token(user)
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    subject = "PortfolioApp - Şifre Sıfırlama"
    body = (
        f"Merhaba {user.first_name},\n\n"
        f"Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:\n"
        f"{reset_link}\n\n"
        "Bu bağlantı 1 saat içinde geçerliliğini yitirecektir.\n\n"
        "Teşekkürler!\nPortfolioApp"
    )

    background_tasks.add_task(send_email_async, user.email, subject, body)
    return {"message": "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi."}

@router.post("/reset-password")
async def reset_password(
    token: str = Query(..., description="Şifre sıfırlama token’ı (mail linkinden gelir)"),
    new_password: str = Query(..., description="Yeni şifre"),
    db: Session = Depends(get_db)
):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş bağlantı.")

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    user.password = hash_password(new_password)
    db.commit()

    subject = "PortfolioApp - Şifreniz Güncellendi"
    body = (
        f"Merhaba {user.first_name},\n\n"
        f"Şifreniz başarıyla sıfırlandı. Eğer bu işlemi siz yapmadıysanız, lütfen hemen giriş yaparak değiştirin.\n\n"
        "PortfolioApp Ekibi"
    )
    await send_email_async(user.email, subject, body)

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
    body = (
        f"Merhaba {current_user.first_name},\n\n"
        "Şifreniz başarıyla değiştirildi. Eğer bu işlemi siz yapmadıysanız, "
        "lütfen hemen giriş yapıp şifrenizi sıfırlayın.\n\n"
        "PortfolioApp Ekibi"
    )
    await send_email_async(current_user.email, subject, body)

    return {"message": "Şifreniz başarıyla güncellendi."}