from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.hosting.schemas import (
    WebsitesResponse, WebsiteCreate, WebsiteUpdate, 
    FTPAccessResponse, FTPAccessCreate, DatabaseResponse, DatabaseCreate
)
from app.modules.auth.routes import get_current_user
from typing import List, Optional

router = APIRouter()


@router.get("/hosting/sites", response_model=List[WebsitesResponse])
async def get_user_sites(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Список сайтов пользователя"""
    # TODO: Получить сайты текущего пользователя
    # TODO: Включить информацию о доменах
    # TODO: Показать статусы сайтов
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.post("/hosting/sites", response_model=WebsitesResponse, status_code=status.HTTP_201_CREATED)
async def create_site(
    site_data: WebsiteCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание сайта (выбор домена, FTP)"""
    # TODO: Проверить права на домен
    # TODO: Создать директорию сайта
    # TODO: Настроить веб-сервер
    # TODO: Создать FTP доступ
    # TODO: Отправить уведомление
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/hosting/sites/{site_id}", response_model=WebsitesResponse)
async def get_site_details(
    site_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Инфо по конкретному сайту"""
    # TODO: Проверить принадлежность сайта пользователю
    # TODO: Получить детальную информацию
    # TODO: Включить статистику сайта
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.delete("/hosting/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление сайта"""
    # TODO: Проверить принадлежность сайта
    # TODO: Удалить файлы сайта
    # TODO: Удалить конфигурацию веб-сервера
    # TODO: Удалить FTP доступ
    # TODO: Уведомить пользователя
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.post("/hosting/sites/{site_id}/ftp", response_model=FTPAccessResponse, status_code=status.HTTP_201_CREATED)
async def create_ftp_access(
    site_id: int,
    ftp_data: FTPAccessCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Генерация FTP-доступа"""
    # TODO: Проверить принадлежность сайта
    # TODO: Создать FTP пользователя
    # TODO: Настроить права доступа
    # TODO: Вернуть данные для подключения
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/hosting/sites/{site_id}/ftp", response_model=List[FTPAccessResponse])
async def get_ftp_access_list(
    site_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список FTP доступов"""
    # TODO: Проверить принадлежность сайта
    # TODO: Получить все FTP аккаунты
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.post("/hosting/sites/{site_id}/db", response_model=DatabaseResponse, status_code=status.HTTP_201_CREATED)
async def create_database(
    site_id: int,
    db_data: DatabaseCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание БД для сайта"""
    # TODO: Проверить принадлежность сайта
    # TODO: Создать базу данных
    # TODO: Создать пользователя БД
    # TODO: Настроить права доступа
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/hosting/sites/{site_id}/db", response_model=List[DatabaseResponse])
async def get_site_databases(
    site_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить базы данных сайта"""
    # TODO: Проверить принадлежность сайта
    # TODO: Получить все БД сайта
    raise HTTPException(status_code=501, detail="Метод не реализован") 