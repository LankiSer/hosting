from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from enum import Enum


class DomainStatus(str, Enum):
    """Статусы доменов"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class DNSRecordType(str, Enum):
    """Типы DNS записей"""
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    PTR = "PTR"


class DomainCreate(BaseModel):
    """Схема создания домена"""
    domain_name: str
    auto_renew: bool = True
    years: int = 1


class DomainUpdate(BaseModel):
    """Схема обновления домена"""
    auto_renew: Optional[bool] = None
    status: Optional[DomainStatus] = None


class DomainResponse(BaseModel):
    """Схема ответа с данными домена"""
    domain_id: int
    domain_name: str
    status: DomainStatus
    registration_date: datetime
    expiration_date: date
    auto_renew: bool
    nameservers: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class DNSRecordCreate(BaseModel):
    """Схема создания DNS записи"""
    record_type: DNSRecordType
    name: str
    value: str
    ttl: int = 3600
    priority: Optional[int] = None


class DNSRecordUpdate(BaseModel):
    """Схема обновления DNS записи"""
    value: Optional[str] = None
    ttl: Optional[int] = None
    priority: Optional[int] = None


class DNSRecordResponse(BaseModel):
    """Схема ответа с данными DNS записи"""
    record_id: int
    record_type: DNSRecordType
    name: str
    value: str
    ttl: int
    priority: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True 