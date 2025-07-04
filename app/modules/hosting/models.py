from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.db import Base


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