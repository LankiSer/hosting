from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.db import Base

# Импорт модели авторизации
from app.modules.auth.models import AuthUsers
from app.modules.notifications.models import Notification
from app.modules.support.models import SupportTicket, SupportSession, SupportMessage, KnowledgeBase


class ResourceLimits(Base):
    __tablename__ = 'resource_limits'
    
    limit_id = Column(Integer, primary_key=True)
    cpu = Column(String(50))
    memory = Column(String(50))
    disk = Column(String(50))
    
    # Отношения
    clients = relationship("Clients", back_populates="resource_limit")


class Clients(Base):
    __tablename__ = 'clients'
    
    client_id = Column(Integer, primary_key=True)
    external_client_id = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    price_monthly = Column(Numeric(10, 2))
    price_yearly = Column(Numeric(10, 2))
    limit_id = Column(Integer, ForeignKey('resource_limits.limit_id'))
    created_at = Column(DateTime, server_default='now()')
    phone = Column(String(50))
    phone_verified = Column(Boolean, default=False)
    email = Column(String(100))
    email_verified = Column(Boolean, default=False)
    last_action = Column(DateTime)
    notice = Column(Text)
    support_tickets = Column(Text)
    
    # Отношения
    resource_limit = relationship("ResourceLimits", back_populates="clients")
    users = relationship("Users", back_populates="client")


class Users(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'))
    username = Column(String(50), unique=True, nullable=False)
    system_uid = Column(String(50))
    system_gid = Column(String(50))
    ftp_id = Column(Integer)
    created_at = Column(DateTime, server_default='now()')
    
    # Отношения
    client = relationship("Clients", back_populates="users")
    websites = relationship("Websites", back_populates="user")


class Statuses(Base):
    __tablename__ = 'statuses'
    
    status_id = Column(Integer, primary_key=True)
    status_name = Column(String(50), nullable=False)
    
    # Отношения
    websites = relationship("Websites", back_populates="status")


class ServerConfigs(Base):
    __tablename__ = 'server_configs'
    
    config_id = Column(Integer, primary_key=True)
    nginx_config_url = Column(Text)
    apache_config_url = Column(Text)
    ssl_cert_url = Column(Text)
    ssl_private_key_url = Column(Text)
    ssl_expiration_date = Column(Date)
    created_at = Column(DateTime, server_default='now()')
    last_updated_at = Column(DateTime)
    
    # Отношения
    websites = relationship("Websites", back_populates="config")


class Websites(Base):
    __tablename__ = 'websites'
    
    site_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    domain_name = Column(String(255), nullable=False)
    directory_path = Column(String(255), nullable=False)
    status_id = Column(Integer, ForeignKey('statuses.status_id'))
    config_id = Column(Integer, ForeignKey('server_configs.config_id'))
    
    # Отношения
    user = relationship("Users", back_populates="websites")
    status = relationship("Statuses", back_populates="websites")
    config = relationship("ServerConfigs", back_populates="websites") 