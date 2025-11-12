from pydantic_settings import BaseSettings
from typing import Optional


DEFAULT_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.153:5173",
    "http://192.168.1.153:4173",
    "http://192.168.0.82:5173",
    "http://192.168.0.82:4173",
]


class Settings(BaseSettings):
    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "hosting"
    db_user: str = "postgres"
    db_password: str = "admin"
    database_echo: bool = False
    
    # JWT settings
    secret_key: str = "your-secret-key-here"
    refresh_secret_key: str = "your-refresh-secret-key-here-different"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API settings
    api_title: str = "Shared Hosting API"
    api_version: str = "1.2.6"

    # ISPmanager settings
    isp_api_base_url: str = "https://192.168.1.153:1500"
    isp_api_token: str | None = None
    isp_admin_login: str | None = None
    isp_admin_password: str | None = None
    isp_default_template: str = "default"
    ftp_root_path: str = "/var/www/clients"
    frontend_origins: list[str] = DEFAULT_FRONTEND_ORIGINS
    frontend_allow_all_origins: bool = True
    isp_enable_sync: bool = True
    isp_verify_ssl: bool = True
    
    # RabbitMQ settings (optional)
    rabbitmq_host: str | None = None
    rabbitmq_port: int = 5672
    rabbitmq_user: str | None = None
    rabbitmq_password: str | None = None
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    class Config:
        env_file = ".env"


settings = Settings() 