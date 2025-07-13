from pydantic import BaseModel, EmailStr, validator, Field
from datetime import datetime
from typing import Optional
import re


class UserRegister(BaseModel):
    """Схема для регистрации пользователя"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну букву')
        if not re.search(r'[0-9]', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        return v

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username может содержать только буквы, цифры, _ и -')
        return v

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v and ('<' in v or '>' in v):
            raise ValueError('Имя не может содержать HTML теги')
        return v


class UserLogin(BaseModel):
    """Схема для входа пользователя"""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя"""
    user_id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email_verified: bool = False
    phone_verified: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Схема JWT токена"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Схема запроса на обновление токена"""
    refresh_token: str


class TokenData(BaseModel):
    """Схема данных токена"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None 