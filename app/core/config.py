from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database settings
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "hosting"
    db_user: str = "postgres"
    db_password: str = "admin"
    
    # RabbitMQ settings
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    
    # JWT settings
    secret_key: str = "your-secret-key-here"
    refresh_secret_key: str = "your-refresh-secret-key-here-different"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API settings
    api_title: str = "Shared Hosting API"
    api_version: str = "1.2.6"
    
    # GigaChat settings
    gigachat_api_key: str = "MTM5ZGVlYzYtMzYwNC00NDVmLWExNjktMDk4NTg0NTRhZDhhOjQxZGJiOGY3LThlY2YtNDgwMS1iNTk5LTZkM2E5NDQyNWE0MQ=="
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"
    
    class Config:
        env_file = ".env"


settings = Settings() 