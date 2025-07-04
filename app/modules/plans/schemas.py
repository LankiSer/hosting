from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class PlanCreate(BaseModel):
    """Схема создания тарифа"""
    name: str
    description: Optional[str] = None
    price_monthly: Decimal
    price_yearly: Optional[Decimal] = None
    cpu_limit: str
    memory_limit: str
    disk_limit: str
    bandwidth_limit: Optional[str] = None
    domains_limit: int = 1
    databases_limit: int = 1
    email_accounts_limit: int = 1
    is_active: bool = True


class PlanUpdate(BaseModel):
    """Схема обновления тарифа"""
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    cpu_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    disk_limit: Optional[str] = None
    bandwidth_limit: Optional[str] = None
    domains_limit: Optional[int] = None
    databases_limit: Optional[int] = None
    email_accounts_limit: Optional[int] = None
    is_active: Optional[bool] = None


class PlanResponse(BaseModel):
    """Схема ответа с данными тарифа"""
    plan_id: int
    name: str
    description: Optional[str] = None
    price_monthly: Decimal
    price_yearly: Optional[Decimal] = None
    cpu_limit: str
    memory_limit: str
    disk_limit: str
    bandwidth_limit: Optional[str] = None
    domains_limit: int
    databases_limit: int
    email_accounts_limit: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True 