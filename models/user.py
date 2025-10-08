# models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from core.database import Base, get_istanbul_now

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    email_verify_token = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=get_istanbul_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_istanbul_now, onupdate=get_istanbul_now)

    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete")