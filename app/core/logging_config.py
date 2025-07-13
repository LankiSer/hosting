"""
Конфигурация логирования для приложения
"""

import os
import logging
import logging.config
from datetime import datetime
from pathlib import Path

# Создаём папку для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Создаём подпапки для разных типов логов
(LOG_DIR / "app").mkdir(exist_ok=True)
(LOG_DIR / "security").mkdir(exist_ok=True)
(LOG_DIR / "auth").mkdir(exist_ok=True)
(LOG_DIR / "database").mkdir(exist_ok=True)
(LOG_DIR / "support").mkdir(exist_ok=True)
(LOG_DIR / "errors").mkdir(exist_ok=True)

# Получаем текущую дату для файлов
current_date = datetime.now().strftime("%Y-%m-%d")

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '{asctime} | {levelname:8} | {name:30} | {funcName:20} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '{asctime} | {levelname:8} | {message}',
            'style': '{',
            'datefmt': '%H:%M:%S'
        },
        'security': {
            'format': '{asctime} | SECURITY | {levelname:8} | {name} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': f'logs/app/app_{current_date}.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'WARNING',
            'formatter': 'security',
            'filename': f'logs/security/security_{current_date}.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'encoding': 'utf8'
        },
        'auth_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': f'logs/auth/auth_{current_date}.log',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'database_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'WARNING',
            'formatter': 'detailed',
            'filename': f'logs/database/database_{current_date}.log',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 3,
            'encoding': 'utf8'
        },
        'support_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': f'logs/support/support_{current_date}.log',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': f'logs/errors/errors_{current_date}.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'encoding': 'utf8'
        }
    },
    'loggers': {
        # Основное приложение
        'app.main': {
            'level': 'INFO',
            'handlers': ['console', 'app_file'],
            'propagate': False
        },
        # Безопасность
        'app.middleware.security': {
            'level': 'WARNING',
            'handlers': ['console', 'security_file'],
            'propagate': False
        },
        # Авторизация
        'app.modules.auth': {
            'level': 'INFO',
            'handlers': ['console', 'auth_file'],
            'propagate': False
        },
        # База данных (SQLAlchemy)
        'sqlalchemy.engine': {
            'level': 'WARNING',
            'handlers': ['database_file'],
            'propagate': False
        },
        'sqlalchemy.pool': {
            'level': 'WARNING',
            'handlers': ['database_file'],
            'propagate': False
        },
        # Поддержка
        'app.modules.support': {
            'level': 'INFO',
            'handlers': ['console', 'support_file'],
            'propagate': False
        },
        # Ошибки
        'uvicorn.error': {
            'level': 'ERROR',
            'handlers': ['error_file'],
            'propagate': False
        },
        'fastapi': {
            'level': 'WARNING',
            'handlers': ['error_file'],
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'app_file', 'error_file']
    }
}

def setup_logging():
    """Настройка логирования"""
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Создаём специальные логгеры
    security_logger = logging.getLogger('app.middleware.security')
    auth_logger = logging.getLogger('app.modules.auth')
    support_logger = logging.getLogger('app.modules.support')
    
    return {
        'security': security_logger,
        'auth': auth_logger,
        'support': support_logger
    }

# Функции для удобного логирования
def log_security_event(event_type: str, message: str, details: dict = None):
    """Логирование события безопасности"""
    logger = logging.getLogger('app.middleware.security')
    log_message = f"{event_type}: {message}"
    if details:
        log_message += f" | Details: {details}"
    logger.warning(log_message)

def log_auth_event(event_type: str, message: str, user_id: str = None):
    """Логирование события авторизации"""
    logger = logging.getLogger('app.modules.auth')
    log_message = f"{event_type}: {message}"
    if user_id:
        log_message += f" | User ID: {user_id}"
    logger.info(log_message)

def log_support_event(event_type: str, message: str, session_id: str = None):
    """Логирование события поддержки"""
    logger = logging.getLogger('app.modules.support')
    log_message = f"{event_type}: {message}"
    if session_id:
        log_message += f" | Session ID: {session_id}"
    logger.info(log_message)

def log_error(error_type: str, message: str, details: dict = None):
    """Логирование ошибки"""
    logger = logging.getLogger('root')
    log_message = f"{error_type}: {message}"
    if details:
        log_message += f" | Details: {details}"
    logger.error(log_message) 