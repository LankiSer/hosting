from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.modules.auth.models import AuthUsers
    from app.modules.domains.models import Domain


class HostingAccount(Base):
    __tablename__ = "hosting_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, unique=True)
    ftp_username = Column(String(100), nullable=False, unique=True)
    ftp_password = Column(Text, nullable=False)
    home_directory = Column(Text, nullable=False)
    isp_ftp_id = Column(String(128))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("AuthUsers", back_populates="hosting_account")


class HostingSite(Base):
    __tablename__ = "hosting_sites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="SET NULL"))
    root_path = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="active")
    isp_site_id = Column(String(128))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("AuthUsers", back_populates="sites")
    domain = relationship("Domain", back_populates="site")