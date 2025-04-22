from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    """用户创建模型"""
    password: str

class UserUpdate(UserBase):
    """用户更新模型"""
    password: Optional[str] = None

class UserInDB(UserBase):
    """数据库用户模型"""
    id: int
    password_hash: str
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 