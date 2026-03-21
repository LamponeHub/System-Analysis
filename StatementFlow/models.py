from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from database import Base

class StatementStatus(enum.Enum):
    DRAFT = "draft"           # Черновик
    SUBMITTED = "submitted"   # Подано
    ANSWERED = "answered"     # Получен ответ

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    telegram_id = Column(String, unique=True, nullable=True)  # Для связи с ботом
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    statements = relationship("Statement", back_populates="owner")

class Statement(Base):
    __tablename__ = "statements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    applicant_name = Column(String, index=True)
    applicant_address = Column(String)
    target_department = Column(String)
    title = Column(String)
    description = Column(Text)
    
    status = Column(Enum(StatementStatus), default=StatementStatus.DRAFT)
    status_updated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("User", back_populates="statements")