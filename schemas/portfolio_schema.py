# schemas/portfolio_schema.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class PortfolioBase(BaseModel):
    title: str
    description: Optional[str] = None
    detail: Optional[str] = None
    link: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    detail: Optional[str] = None
    link: Optional[str] = None

class PortfolioResponseBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    detail: Optional[str] = None
    link: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PortfolioResponse(PortfolioResponseBase):
    user_id: int

class PortfolioUserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True

class PortfolioDetailResponse(PortfolioResponseBase):
    user: PortfolioUserResponse