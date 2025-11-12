#!/usr/bin/env python3
"""
Скрипт для быстрого запуска Shared Hosting API
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8009,
        reload=False,
        log_level="info",
        reload_excludes=[
            "*.log",
            "logs/*",
            "logs/**/*",
            "__pycache__/*",
            "**/__pycache__/*",
            "*.pyc",
            "**/*.pyc",
            ".git/*",
            ".idea/*",
            ".venv/*"
        ]
    ) 