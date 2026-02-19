import enum

from sqlalchemy import ForeignKey, func, JSON, Identity, BigInteger
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.postgresql import TIMESTAMP
from core.config import Base
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    func,
    text,
    Text,
)


class PaymentStatus(enum.Enum):
    pending = "pending"
    waiting_for_capture = "waiting_for_capture"
    succeeded = "succeeded"
    canceled = "canceled"


class PaymentType(enum.Enum):
    yoo_money = "yoo_money"
    bank_card = "bank_card"


class Payments(Base):
    """
    payment_id - ID конкретного платежа
    payment_method_id - ID сохранённого способа оплаты
    """

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    payment_id: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    price: Mapped[int] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    type: Mapped[PaymentType] = mapped_column(
        SQLEnum(PaymentType, name="type"), nullable=True, name="type"
    )
    payment_method_id: Mapped[str] = mapped_column(Text, nullable=True)
    payment_details: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name="status"),
        nullable=True,
        name="status",
    )
    payment_for_linking: Mapped[bool] = mapped_column(nullable=True)
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


"""
payment_details
            Для карт
      "card_type": "MasterCard",
      "expiry_month": "11",
      "expiry_year": "2011",
      "first6": "555555",
      "issuer_country": "US",
      "last4": "4477"
            Для yoomoney
      "title": "YooMoney wallet 410011758831136",
      "type": "yoo_money"
"""
