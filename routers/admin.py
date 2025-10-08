# routers/admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.portfolio import Portfolio
from schemas.user_schema import AdminUserCreate, UserResponse, AdminUserUpdate
from schemas.portfolio_schema import PortfolioResponse, PortfolioUpdate
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
def get_all_users_as_admin(db: Session = Depends(get_db), _: User = Depends(admin_required)):
    return db.query(User).all()

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_as_admin(
        user_data: AdminUserCreate,
        db: Session = Depends(get_db),
        _: User = Depends(admin_required)
):
    existing_user = db.query(User).filter(
        or_(User.username == user_data.username, User.email == str(user_data.email))
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bu e-posta veya kullanıcı adı zaten mevcut.")

    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        email=str(user_data.email),
        password=hash_password(user_data.password),
        is_admin=bool(user_data.is_admin),
        is_verified=bool(user_data.is_verified)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_as_admin(
        user_id: int,
        user_update: AdminUserUpdate,
        db: Session = Depends(get_db),
        _: User = Depends(admin_required)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    update_data = user_update.model_dump(exclude_unset=True)

    if 'email' in update_data:
        update_data['email'] = str(update_data['email'])

    for field, value in update_data.items():
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

    db.query(Portfolio).filter(Portfolio.user_id == user.id).delete()
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
    return portfolios

@router.put("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio_as_admin(
        portfolio_id: int,
        portfolio_data: PortfolioUpdate,
        db: Session = Depends(get_db),
        _: User = Depends(admin_required)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio bulunamadı.")

    update_data = portfolio_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(portfolio, key, value)

    db.commit()
    db.refresh(portfolio)
    return portfolio

@router.delete("/portfolios/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio_as_admin(
        portfolio_id: int,
        db: Session = Depends(get_db),
        _: User = Depends(admin_required)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio bulunamadı.")

    db.delete(portfolio)
    db.commit()
    return None