from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
from enum import Enum


class WebsiteStatus(str, Enum):
    """Статусы сайтов"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"


class StatusesBase(BaseModel):
    status_name: str


class StatusesCreate(StatusesBase):
    pass


class StatusesResponse(StatusesBase):
    status_id: int
    
    class Config:
        from_attributes = True


class ServerConfigsBase(BaseModel):
    nginx_config_url: Optional[str] = None
    apache_config_url: Optional[str] = None
    ssl_cert_url: Optional[str] = None
    ssl_private_key_url: Optional[str] = None
    ssl_expiration_date: Optional[date] = None


class ServerConfigsCreate(ServerConfigsBase):
    pass


class ServerConfigsResponse(ServerConfigsBase):
    config_id: int
    created_at: datetime
    last_updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WebsitesBase(BaseModel):
    domain_name: str
    directory_path: str


class WebsiteCreate(WebsitesBase):
    user_id: Optional[int] = None
    status_id: Optional[int] = None
    config_id: Optional[int] = None


class WebsiteUpdate(BaseModel):
    """Схема обновления сайта"""
    domain_name: Optional[str] = None
    directory_path: Optional[str] = None
    status_id: Optional[int] = None
    config_id: Optional[int] = None


class WebsitesResponse(WebsitesBase):
    site_id: int
    user_id: Optional[int] = None
    status_id: Optional[int] = None
    config_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Схемы для FTP доступа
class FTPAccessCreate(BaseModel):
    """Схема создания FTP доступа"""
    username: str
    password: str
    path: Optional[str] = None
    read_only: bool = False


class FTPAccessResponse(BaseModel):
    """Схема ответа FTP доступа"""
    ftp_id: int
    username: str
    path: str
    read_only: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Схемы для баз данных
class DatabaseCreate(BaseModel):
    """Схема создания базы данных"""
    db_name: str
    db_user: str
    db_password: str
    db_type: str = "mysql"


class DatabaseResponse(BaseModel):
    """Схема ответа базы данных"""
    db_id: int
    db_name: str
    db_user: str
    db_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True 