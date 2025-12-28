from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal

class User(BaseModel):
    id: Optional[int] = None
    telegram_id: int
    username: Optional[str] = None
    isAudio: Optional[bool] = False
    notification: Optional[bool] = False
    timezone: Optional[str] = "UTC"  # User's timezone (e.g., "Europe/Berlin", "UTC")
    book_received: Optional[bool] = False  # Track if user received the vitamin book
    lottery_participated: Optional[bool] = False  # Track if user participated in New Year lottery
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class NotificationSettings(BaseModel):
    id: Optional[int] = None
    user_id: int
    settings: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PaymentProduct(BaseModel):
    """Payment product/service model"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price_amount: Decimal
    price_currency: str = "RUB"
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PaymentTransaction(BaseModel):
    """Payment transaction model"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    telegram_id: int
    product_id: Optional[int] = None

    # YooKassa fields
    yookassa_payment_id: Optional[str] = None
    idempotence_key: str

    # Payment details
    amount: Decimal
    currency: str = "RUB"
    status: str = "pending"

    # Confirmation
    confirmation_url: Optional[str] = None
    confirmation_type: Optional[str] = None

    # Payment method
    payment_method_type: Optional[str] = None
    paid_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None

    # Additional
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None