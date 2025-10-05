from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from schemas.user_schema import UserUpdate, UserResponse
from models.user import User
from models.portfolio import Portfolio
from core.security import create_access_token, decode_access_token
from helpers.email_sender import send_email_async
from core.config import BASE_URL

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
        if db.query(User).filter(User.username == user_update.username, User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanılıyor.")
        current_user.username = user_update.username
        updated = True
    if user_update.email:
        if db.query(User).filter(User.email == user_update.email, User.id != current_user.id).first():
            raise HTTPException(status_code=400, detail="Bu e-posta zaten kullanılıyor.")
        if user_update.email != current_user.email:
            email_changed = True
            current_user.email = user_update.email
            current_user.is_verified = False
            updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="Güncellenecek bir bilgi bulunamadı.")

    db.commit()
    db.refresh(current_user)

    if email_changed:
        token = create_access_token(current_user)
        verify_link = f"{BASE_URL}/auth/verify-email?token={token}"

        subject = "PortfolioApp - Yeni E-posta Doğrulama"
        body = (
            f"Merhaba {current_user.first_name},\n\n"
            f"E-posta adresinizi güncellediniz.\n"
            f"Yeni adresinizi doğrulamak için aşağıdaki bağlantıya tıklayın:\n"
            f"{verify_link}\n\n"
            "Doğrulama yapılmadan giriş yapamazsınız.\n\n"
            "Teşekkürler!\nPortfolioApp"
        )

        background_tasks.add_task(send_email_async, current_user.email, subject, body)

        return JSONResponse(
            status_code=202,
            content={
                "message": "Bilgiler güncellendi. Yeni e-posta adresinize doğrulama gönderildi, lütfen giriş yapmadan önce doğrulayın.",
                "logout_required": True
            }
        )

    return current_user

@router.post("/request-delete")
async def request_account_deletion(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    token = create_access_token(current_user)
    delete_link = f"{BASE_URL}/users/confirm-delete?token={token}"

    subject = "PortfolioApp - Hesap Silme Onayı"
    body = (
        f"Merhaba {current_user.first_name},\n\n"
        f"Hesabınızı silmek istediğinizi belirttiniz.\n"
        f"Bu işlemi onaylamak için aşağıdaki bağlantıya tıklayın:\n"
        f"{delete_link}\n\n"
        "Eğer bu işlemi siz başlatmadıysanız, bu e-postayı dikkate almayın.\n\n"
        "Teşekkürler!\nPortfolioApp"
    )

    background_tasks.add_task(send_email_async, current_user.email, subject, body)
    return {"message": "Hesap silme onay maili gönderildi."}

@router.get("/confirm-delete")
async def confirm_account_deletion(token: str, db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Geçersiz veya süresi dolmuş bağlantı.")

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    email = user.email
    first_name = user.first_name

    db.query(Portfolio).filter(Portfolio.user_id == user.id).delete()

    db.delete(user)
    db.commit()

    subject = "PortfolioApp - Hesabınız Silindi"
    body = (
        f"Merhaba {first_name},\n\n"
        f"Hesabınız ve portfolyolarınız başarıyla silindi.\n"
        f"Eğer bu işlemi siz yapmadıysanız, lütfen hemen bizimle iletişime geçin.\n\n"
        "Teşekkürler!\nPortfolioApp"
    )

    try:
        await send_email_async(email, subject, body)
    except Exception:
        pass

    return {"message": "Hesabınız ve portfolyolarınız başarıyla silindi."}