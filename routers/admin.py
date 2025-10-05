from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.portfolio import Portfolio
from schemas.user_schema import UserCreate, UserResponse, UserUpdate
from schemas.portfolio_schema import PortfolioResponse
from core.security import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])

def admin_required(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlemi yapmak için admin yetkisine sahip olmanız gerekir."
        )
    return current_user

@router.get("/users", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return db.query(User).all()

@router.post("/users", response_model=UserResponse)
def create_user_as_admin(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu kullanıcı zaten mevcut.")

    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        email=user_data.email,
        password=hash_password(user_data.password),
        is_admin=False,
        is_verified=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_as_admin(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_as_admin(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    db.delete(user)
    db.commit()
    return None

@router.get("/portfolios/{user_id}", response_model=list[PortfolioResponse])
def get_user_portfolios_as_admin(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    if not portfolios:
        raise HTTPException(status_code=404, detail="Bu kullanıcıya ait portfolio bulunamadı.")
    return portfolios

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_as_admin(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    db.query(Portfolio).filter(Portfolio.user_id == user.id).delete()

    db.delete(user)
    db.commit()

    return None