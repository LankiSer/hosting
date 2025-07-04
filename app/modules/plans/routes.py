from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.plans.schemas import PlanResponse, PlanCreate, PlanUpdate
from app.modules.auth.routes import get_current_user
from typing import List, Optional

router = APIRouter()


@router.get("/plans", response_model=List[PlanResponse])
async def get_available_plans(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Список доступных тарифов"""
    # TODO: Получить активные тарифы
    # TODO: Применить пагинацию
    # TODO: Скрыть внутренние тарифы
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создание тарифа (админка)"""
    # TODO: Проверить права администратора
    # TODO: Создать тариф в БД
    # TODO: Логировать создание тарифа
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan_details(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Информация по тарифу"""
    # TODO: Получить детали тарифа
    # TODO: Проверить активность тарифа
    # TODO: Включить лимиты ресурсов
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_update: PlanUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление тарифа (админка)"""
    # TODO: Проверить права администратора
    # TODO: Обновить тариф в БД
    # TODO: Уведомить пользователей об изменениях
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаление тарифа"""
    # TODO: Проверить права администратора
    # TODO: Проверить использование тарифа
    # TODO: Деактивировать тариф
    raise HTTPException(status_code=501, detail="Метод не реализован") 