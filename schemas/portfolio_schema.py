from pydantic import BaseModel
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

class PortfolioResponse(PortfolioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: int

    class Config:
        from_attributes = True