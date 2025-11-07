from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.modules.auth.models import AuthUsers
    from app.modules.hosting.models import HostingSite


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, unique=True)
    status = Column(String(32), nullable=False, default="pending")
    auto_renew = Column(Boolean, nullable=False, default=True)
    expires_at = Column(Date)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    isp_domain_id = Column(String(128))
    nameservers = Column(ARRAY(String(255)))

    user = relationship("AuthUsers", back_populates="domains")
    dns_records = relationship("DNSRecord", back_populates="domain", cascade="all, delete-orphan")
    site = relationship("HostingSite", back_populates="domain", uselist=False)


class DNSRecord(Base):
    __tablename__ = "dns_records"

    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True)
    record_type = Column(String(16), nullable=False)
    name = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    ttl = Column(Integer, nullable=False, default=3600)
    priority = Column(Integer)
    isp_record_id = Column(String(128))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    domain = relationship("Domain", back_populates="dns_records")

