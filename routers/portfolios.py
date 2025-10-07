from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from schemas.portfolio_schema import PortfolioCreate, PortfolioUpdate, PortfolioResponse
from models.portfolio import Portfolio
from models.user import User

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])

@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    portfolio_data: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    new_portfolio = Portfolio(**portfolio_data.dict(), user_id=current_user.id)
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

@router.get("/all_portfolios")
def list_all_portfolios(db: Session = Depends(get_db)):
    results = (
        db.query(Portfolio, User)
        .join(User, User.id == Portfolio.user_id)
        .all()
    )
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "detail": p.detail,
            "link": p.link,
            "user_id": u.id,
            "user": {
                "id": u.id,
                "username": u.username,
                "email": u.email
            }
        }
        for (p, u) in results
    ]

@router.get("/{portfolio_id:int}")
def get_portfolio_detail(
    portfolio_id: int,
    db: Session = Depends(get_db),
):
    result = (
        db.query(Portfolio, User)
        .join(User, User.id == Portfolio.user_id)
        .filter(Portfolio.id == portfolio_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Portfolio bulunamadı.")

    p, u = result
    return {
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "detail": p.detail,
        "link": p.link,
        "user_id": u.id,
        "user": {
            "id": u.id,
            "username": u.username,
            "email": u.email
        }
    }

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

    for key, value in portfolio_data.dict(exclude_unset=True).items():
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