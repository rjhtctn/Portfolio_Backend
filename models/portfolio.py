# models/portfolio.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from core.database import Base, get_istanbul_now

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    detail = Column(Text, nullable=True)
    link = Column(String(255), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), default=get_istanbul_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_istanbul_now, onupdate=get_istanbul_now)

    user = relationship("User", back_populates="portfolios")