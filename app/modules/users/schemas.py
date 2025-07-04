from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class ResourceLimitsBase(BaseModel):
    cpu: Optional[str] = None
    memory: Optional[str] = None
    disk: Optional[str] = None


class ResourceLimitsCreate(ResourceLimitsBase):
    pass


class ResourceLimitsResponse(ResourceLimitsBase):
    limit_id: int
    
    class Config:
        from_attributes = True


class ClientsBase(BaseModel):
    external_client_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    phone: Optional[str] = None
    phone_verified: bool = False
    email: Optional[str] = None
    email_verified: bool = False
    notice: Optional[str] = None
    support_tickets: Optional[str] = None


class ClientsCreate(ClientsBase):
    limit_id: Optional[int] = None


class ClientsResponse(ClientsBase):
    client_id: int
    limit_id: Optional[int] = None
    created_at: datetime
    last_action: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UsersBase(BaseModel):
    username: str
    system_uid: Optional[str] = None
    system_gid: Optional[str] = None
    ftp_id: Optional[int] = None


class UsersCreate(UsersBase):
    client_id: Optional[int] = None


class UsersUpdate(BaseModel):
    """Схема обновления пользователя"""
    username: Optional[str] = None
    system_uid: Optional[str] = None
    system_gid: Optional[str] = None
    ftp_id: Optional[int] = None


class UsersResponse(UsersBase):
    user_id: int
    client_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 