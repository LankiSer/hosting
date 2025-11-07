from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.modules.domains.models import Domain
    from app.modules.hosting.models import HostingAccount, HostingSite


class AuthUsers(Base):
    """Основная учетная запись пользователя платформы."""

    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)

    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))

    is_active = Column(Boolean, nullable=False, default=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    phone_verified = Column(Boolean, nullable=False, default=False)

    isp_account_id = Column(String(128))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    hosting_account = relationship("HostingAccount", back_populates="user", uselist=False)
    domains = relationship("Domain", back_populates="user", cascade="all, delete-orphan")
    sites = relationship("HostingSite", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<AuthUser email={self.email!r} username={self.username!r}>"