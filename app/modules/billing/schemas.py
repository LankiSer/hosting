from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    """Типы транзакций"""
    PAYMENT = "payment"
    REFUND = "refund"
    CHARGE = "charge"
    BONUS = "bonus"


class TransactionStatus(str, Enum):
    """Статусы транзакций"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Способы оплаты"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    CRYPTOCURRENCY = "cryptocurrency"


class PaymentCreate(BaseModel):
    """Схема создания платежа"""
    amount: Decimal
    payment_method: PaymentMethod
    description: Optional[str] = None
    return_url: Optional[str] = None


class PaymentResponse(BaseModel):
    """Схема ответа платежа"""
    payment_id: int
    amount: Decimal
    payment_method: PaymentMethod
    status: TransactionStatus
    payment_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Схема ответа транзакции"""
    transaction_id: int
    type: TransactionType
    amount: Decimal
    status: TransactionStatus
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """Схема ответа счета"""
    invoice_id: int
    invoice_number: str
    amount: Decimal
    status: TransactionStatus
    description: Optional[str] = None
    created_at: datetime
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 