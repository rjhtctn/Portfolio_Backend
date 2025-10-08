# core/security.py

from datetime import timedelta
from fastapi import HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from core.database import get_istanbul_now

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict, token_type: str, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    now = get_istanbul_now()

    if expires_delta is None:
        if token_type == "access":
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expires_delta = timedelta(minutes=15)

    to_encode.update({
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str, expected_type: str = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token geçersiz veya süresi dolmuş.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if expected_type and payload.get("type") != expected_type:
            raise credentials_exception

        return payload
    except JWTError:
        raise credentials_exception