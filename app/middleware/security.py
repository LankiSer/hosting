"""
Middleware для безопасности FastAPI приложения
"""

import logging
import time
from typing import Dict, Set
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import re
import json
from urllib.parse import unquote

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware для обеспечения безопасности приложения
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'expression\s*\(',
            r'vbscript:',
            r'data:text/html',
            r'<svg[^>]*onload',
            r'<img[^>]*onerror'
        ]
        
        # Подозрительные user agents
        self.suspicious_user_agents = [
            'sqlmap',
            'nmap',
            'nikto',
            'burp',
            'dirbuster',
            'gobuster',
            'wpscan',
            'masscan'
        ]
        
        # Подозрительные пути
        self.suspicious_paths = [
            '/admin',
            '/wp-admin',
            '/phpmyadmin',
            '/config',
            '/env',
            '/.env',
            '/backup',
            '/db',
            '/database',
            '/sql',
            '/phpinfo',
            '/test',
            '/debug'
        ]
        
        # Кеш для rate limiting (в продакшене использовать Redis)
        self.rate_limit_cache: Dict[str, list] = {}
        
    async def dispatch(self, request: Request, call_next):
        """
        Обработка запроса
        """
        start_time = time.time()
        
        # Проверяем подозрительную активность
        if self._is_suspicious_request(request):
            logger.warning(f"Подозрительный запрос: {request.url} от {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Forbidden"}
            )
        
        # Проверяем XSS в параметрах (отключено)
        # if self._check_xss_in_request(request):
        #     logger.warning(f"XSS попытка в запросе: {request.url}")
        #     return JSONResponse(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         content={"detail": "Недопустимые данные"}
        #     )
        
        # Простой rate limiting
        if self._is_rate_limited(request):
            logger.warning(f"Rate limit превышен для {request.client.host}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Слишком много запросов"}
            )
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Добавляем заголовки безопасности
        response = self._add_security_headers(response)
        
        # Логируем запрос
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.4f}s")
        
        return response
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """
        Проверка на подозрительные запросы
        """
        # Проверяем User-Agent
        user_agent = request.headers.get('user-agent', '').lower()
        for suspicious_agent in self.suspicious_user_agents:
            if suspicious_agent in user_agent:
                return True
        
        # Проверяем путь
        path = request.url.path.lower()
        for suspicious_path in self.suspicious_paths:
            if suspicious_path in path:
                return True
        
        # Проверяем на SQL injection паттерны
        query_params = str(request.url.query).lower()
        sql_patterns = [
            'union select',
            'or 1=1',
            'and 1=1',
            '\'or\'',
            '\'and\'',
            'drop table',
            'delete from',
            'insert into',
            'update set',
            'exec(',
            'system(',
            'cmd.exe',
            '/etc/passwd',
            '../../'
        ]
        
        for pattern in sql_patterns:
            if pattern in query_params or pattern in path:
                return True
        
        return False
    
    def _check_xss_in_request(self, request: Request) -> bool:
        """
        Проверка на XSS в параметрах запроса
        """
        # Проверяем query параметры
        query_string = str(request.url.query)
        if query_string:
            decoded_query = unquote(query_string)
            for pattern in self.xss_patterns:
                if re.search(pattern, decoded_query, re.IGNORECASE):
                    return True
        
        # Проверяем путь
        path = unquote(request.url.path)
        for pattern in self.xss_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        return False
    
    def _is_rate_limited(self, request: Request) -> bool:
        """
        Простая проверка rate limiting
        """
        client_ip = request.client.host
        current_time = time.time()
        
        # Убираем старые записи (старше 60 секунд)
        if client_ip in self.rate_limit_cache:
            self.rate_limit_cache[client_ip] = [
                timestamp for timestamp in self.rate_limit_cache[client_ip]
                if current_time - timestamp < 60
            ]
        else:
            self.rate_limit_cache[client_ip] = []
        
        # Проверяем лимит (60 запросов в минуту)
        if len(self.rate_limit_cache[client_ip]) >= 60:
            return True
        
        # Добавляем текущий запрос
        self.rate_limit_cache[client_ip].append(current_time)
        
        return False
    
    def _add_security_headers(self, response: Response) -> Response:
        """
        Добавление заголовков безопасности
        """
        # Предотвращение clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Предотвращение MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=(), vibrate=(), fullscreen=(), notifications=()"
        
        # Strict Transport Security (только для HTTPS)
        if hasattr(response, 'headers') and 'https' in str(response.headers.get('location', '')):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware для санитизации входящих данных
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object',
            r'<embed',
            r'<link',
            r'<meta',
            r'expression\s*\(',
            r'vbscript:',
            r'data:text/html'
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Обработка запроса с санитизацией данных
        """
        # Пропускаем auth endpoints без санитизации
        if request.url.path.startswith('/auth/'):
            return await call_next(request)
        
        # Получаем тело запроса один раз
        body = await request.body()
        
        # Воссоздаём request с сохранённым телом
        async def receive():
            return {'type': 'http.request', 'body': body}
        
        request._receive = receive
        
        # Только базовая проверка на опасные паттерны
        if body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body_str = body.decode('utf-8', errors='ignore')
                
                # Проверяем только самые опасные паттерны
                if '<script' in body_str.lower() or 'javascript:' in body_str.lower():
                    logger.warning(f"Обнаружен опасный скрипт в запросе: {request.url}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Недопустимые данные"}
                    )
                        
            except Exception as e:
                logger.error(f"Ошибка при проверке тела запроса: {e}")
        
        return await call_next(request)
    
    def _sanitize_data(self, data) -> any:
        """
        Рекурсивная санитизация данных
        """
        if isinstance(data, dict):
            return {
                key: self._sanitize_data(value)
                for key, value in data.items()
                if not self._contains_dangerous_patterns(str(key))
            }
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """
        Санитизация строки
        """
        if not text:
            return text
        
        # Удаляем опасные паттерны
        sanitized = text
        for pattern in self.dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Экранируем HTML символы
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        for char, escaped in html_escape_table.items():
            sanitized = sanitized.replace(char, escaped)
        
        return sanitized
    
    def _contains_dangerous_patterns(self, text: str) -> bool:
        """
        Проверка на опасные паттерны
        """
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


class SecurityLogger:
    """
    Класс для логирования событий безопасности
    """
    
    @staticmethod
    def log_security_event(event_type: str, details: dict, request: Request = None):
        """
        Логирование события безопасности
        """
        log_entry = {
            'timestamp': time.time(),
            'event_type': event_type,
            'details': details,
            'ip': request.client.host if request else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown') if request else 'unknown',
            'url': str(request.url) if request else 'unknown'
        }
        
        logger.warning(f"SECURITY EVENT: {json.dumps(log_entry)}")
        
        # В продакшене отправлять в систему мониторинга
        # например, в ELK Stack, Splunk, или другую SIEM систему
    
    @staticmethod
    def log_auth_attempt(success: bool, email: str, ip: str, user_agent: str):
        """
        Логирование попытки аутентификации
        """
        SecurityLogger.log_security_event(
            'AUTH_ATTEMPT',
            {
                'success': success,
                'email': email,
                'ip': ip,
                'user_agent': user_agent
            }
        )
    
    @staticmethod
    def log_xss_attempt(payload: str, ip: str, user_agent: str):
        """
        Логирование попытки XSS
        """
        SecurityLogger.log_security_event(
            'XSS_ATTEMPT',
            {
                'payload': payload[:200],  # Ограничиваем размер
                'ip': ip,
                'user_agent': user_agent
            }
        )
    
    @staticmethod
    def log_suspicious_activity(activity_type: str, details: dict, ip: str):
        """
        Логирование подозрительной активности
        """
        SecurityLogger.log_security_event(
            'SUSPICIOUS_ACTIVITY',
            {
                'activity_type': activity_type,
                'details': details,
                'ip': ip
            }
        ) 