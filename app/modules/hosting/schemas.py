from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SiteStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DISABLED = "disabled"


class HostingSiteCreate(BaseModel):
    domain_id: Optional[int] = None
    root_path: str


class HostingSiteResponse(BaseModel):
    id: int
    domain_id: Optional[int] = None
    root_path: str
    status: SiteStatus
    isp_site_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HostingAccountResponse(BaseModel):
    ftp_username: str
    ftp_password: str
    home_directory: str

    class Config:
        from_attributes = True