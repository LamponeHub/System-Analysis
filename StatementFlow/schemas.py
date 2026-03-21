from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class StatementStatusEnum(str, Enum):
    draft = "draft"
    submitted = "submitted"
    answered = "answered"

# === User Schemas ===
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    telegram_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# === Statement Schemas ===
class StatementBase(BaseModel):
    applicant_name: str
    applicant_address: str
    target_department: str
    title: str
    description: str
    status: StatementStatusEnum = StatementStatusEnum.draft

class StatementCreate(StatementBase):
    pass

class StatementUpdate(BaseModel):
    applicant_name: Optional[str] = None
    applicant_address: Optional[str] = None
    target_department: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StatementStatusEnum] = None

class StatementResponse(StatementBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    status_updated_at: datetime
    
    class Config:
        from_attributes = True

# === Token ===
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None