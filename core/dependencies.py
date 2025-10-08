# core/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.database import get_db
from models.user import User
from core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Oturum geçersiz veya süresi dolmuş.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token, expected_type="access")

    user_id: int = payload.get("user_id")
    email: str = payload.get("email")
    username: str = payload.get("username")

    if not user_id or not email or not username:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception

    if user.email != email or user.username != username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı bilgileri değişti, lütfen tekrar giriş yapın."
        )

    return user