from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Genel amaçlı token üretici
def _create_token(payload: dict, minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    now = datetime.utcnow()
    data = payload.copy()
    data["iat"] = now
    data["exp"] = now + timedelta(minutes=minutes)
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

# ⬅️ Var olan access token fonksiyonun aynen dursun
def create_access_token(user):
    payload = {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
    }
    return _create_token(payload, ACCESS_TOKEN_EXPIRE_MINUTES)

# ✅ Yeni: e-posta doğrulama için nonce (evt) içeren token
def create_email_verify_token(user, evt: str, minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    payload = {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "evt": evt,
    }
    return _create_token(payload, minutes)

def decode_access_token(token: str, db=None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not db:
            return payload

        from models.user import User
        user = db.query(User).filter(User.id == payload.get("user_id")).first()
        if not user:
            return None

        if user.email != payload.get("email") or user.username != payload.get("username"):
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None