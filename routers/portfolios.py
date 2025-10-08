# routers/portfolios.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from core.database import get_db
from core.dependencies import get_current_user
from schemas.portfolio_schema import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioDetailResponse
)
from models.portfolio import Portfolio

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])

@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
        portfolio_data: PortfolioCreate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    new_portfolio_data = portfolio_data.model_dump()
    new_portfolio = Portfolio(**new_portfolio_data, user_id=current_user.id)

    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    return new_portfolio

@router.get("/my_portfolios", response_model=list[PortfolioResponse])
def get_my_portfolios(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    return portfolios

@router.get("/all_portfolios", response_model=list[PortfolioDetailResponse])
def list_all_portfolios(db: Session = Depends(get_db)):
    portfolios = db.query(Portfolio).options(joinedload(Portfolio.user)).all()
    return portfolios

@router.get("/{portfolio_id:int}", response_model=PortfolioDetailResponse)
def get_portfolio_detail(
        portfolio_id: int,
        db: Session = Depends(get_db),
):
    portfolio = db.query(Portfolio).options(joinedload(Portfolio.user)).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio bulunamadı.")
    return portfolio

@router.put("/{portfolio_id:int}", response_model=PortfolioResponse)
def update_portfolio(
        portfolio_id: int,
        portfolio_data: PortfolioUpdate,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio bulunamadı.")

    update_data = portfolio_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(portfolio, key, value)

    db.commit()
    db.refresh(portfolio)
    return portfolio

@router.delete("/{portfolio_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
        portfolio_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio bulunamadı.")

    db.delete(portfolio)
    db.commit()
    return None

@router.get("/user/{user_id:int}", response_model=list[PortfolioDetailResponse])
def list_user_portfolios_by_id(
        user_id: int,
        db: Session = Depends(get_db),
):
    portfolios = (
        db.query(Portfolio)
        .options(joinedload(Portfolio.user))
        .filter(Portfolio.user_id == user_id)
        .all()
    )
    return portfolios