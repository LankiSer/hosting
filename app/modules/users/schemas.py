from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class HostingAccountInfo(BaseModel):
    ftp_username: str
    home_directory: str

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email_verified: bool
    phone_verified: bool
    isp_account_id: Optional[str] = None
    created_at: datetime
    hosting_account: Optional[HostingAccountInfo] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None