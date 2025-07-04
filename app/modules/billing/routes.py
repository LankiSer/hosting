from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.billing.schemas import (
    TransactionResponse, PaymentCreate, PaymentResponse, InvoiceResponse
)
from app.modules.auth.routes import get_current_user
from typing import List, Optional

router = APIRouter()


@router.get("/billing/history", response_model=List[TransactionResponse])
async def get_transaction_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """История транзакций"""
    # TODO: Получить транзакции пользователя
    # TODO: Применить пагинацию
    # TODO: Сортировать по дате
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.post("/billing/pay", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Пополнение счета или оплата услуг"""
    # TODO: Проверить данные платежа
    # TODO: Создать платеж в БД
    # TODO: Интеграция с платежной системой
    # TODO: Отправить уведомление об оплате
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/billing/balance")
async def get_account_balance(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить баланс счета"""
    # TODO: Получить текущий баланс
    # TODO: Включить информацию о задолженности
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/billing/invoice/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Скачивание или просмотр счета-фактуры"""
    # TODO: Проверить принадлежность инвойса
    # TODO: Получить данные инвойса
    # TODO: Сгенерировать PDF если нужно
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/billing/invoices", response_model=List[InvoiceResponse])
async def get_invoices_list(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Список счетов пользователя"""
    # TODO: Получить все инвойсы пользователя
    # TODO: Применить пагинацию
    raise HTTPException(status_code=501, detail="Метод не реализован") 