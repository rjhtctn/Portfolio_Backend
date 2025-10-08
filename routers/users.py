# routers/users.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import secrets
from core.database import get_db
from core.dependencies import get_current_user
from schemas.user_schema import UserUpdate, UserResponse
from models.user import User
from models.portfolio import Portfolio
from core.security import create_token, decode_token
from helpers.email_sender import send_email_async
from core.config import FRONTEND_URL

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
        user_update: UserUpdate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    updated = False
    email_changed = False

    if user_update.first_name:
        current_user.first_name = user_update.first_name
        updated = True
    if user_update.last_name:
        current_user.last_name = user_update.last_name
        updated = True

    if user_update.username:
        existing_user = db.query(User).filter_by(username=user_update.username).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanılıyor.")
        current_user.username = user_update.username
        updated = True

    if user_update.email:
        email_str = str(user_update.email)
        existing_email_user = db.query(User).filter(User.email.ilike(email_str)).first()
        if existing_email_user and existing_email_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Bu e-posta zaten kullanılıyor.")

        if email_str != current_user.email:
            email_changed = True
            current_user.email = email_str
            current_user.is_verified = False
            evt = secrets.token_hex(16)
            current_user.email_verify_token = evt
            updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="Güncellenecek bir bilgi bulunamadı.")

    db.commit()
    db.refresh(current_user)

    if email_changed:
        token_payload = {"user_id": current_user.id, "evt": current_user.email_verify_token}
        token = create_token(token_payload, token_type="email_verify")
        verify_link = f"{FRONTEND_URL}/verify-email?token={token}"

        subject = "PortfolioApp - Yeni E-posta Doğrulama"
        body = f"Merhaba {current_user.first_name},\n\nYeni e-posta adresinizi doğrulamak için linke tıklayın:\n{verify_link}"
        background_tasks.add_task(send_email_async, current_user.email, subject, body)

        return JSONResponse(
            status_code=202,
            content={
                "message": "Bilgiler güncellendi. Yeni e-posta adresinize doğrulama gönderildi.",
                "logout_required": True
            }
        )

    return current_user


@router.post("/request-delete")
async def request_account_deletion(
        background_tasks: BackgroundTasks,
        current_user: User = Depends(get_current_user)
):
    token_payload = {"user_id": current_user.id}
    token = create_token(token_payload, token_type="account_delete")
    delete_link = f"{FRONTEND_URL}/confirm-delete?token={token}"

    subject = "PortfolioApp - Hesap Silme Onayı"
    body = f"Merhaba {current_user.first_name},\n\nHesabınızı silme işlemini onaylamak için linke tıklayın:\n{delete_link}"
    background_tasks.add_task(send_email_async, current_user.email, subject, body)
    return {"message": "Hesap silme onay maili gönderildi."}


@router.get("/confirm-delete")
async def confirm_account_deletion(token: str, db: Session = Depends(get_db)):
    payload = decode_token(token, expected_type="account_delete")
    user = db.query(User).filter_by(id=payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    email = user.email
    first_name = user.first_name

    db.query(Portfolio).filter_by(user_id=user.id).delete()
    db.delete(user)
    db.commit()

    subject = "PortfolioApp - Hesabınız Silindi"
    body = f"Merhaba {first_name},\n\nHesabınız ve tüm verileriniz başarıyla silindi."
    await send_email_async(str(email), subject, body)

    return {"message": "Hesabınız ve portfolyolarınız başarıyla silindi."}