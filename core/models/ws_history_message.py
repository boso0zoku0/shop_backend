import enum
import datetime as dt
import uuid
from typing import Optional

from sqlalchemy import func, ForeignKey, String, Integer, DateTime, Enum, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from core.config import Base
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy import (
    Text,
    Identity,
    create_engine,
    CheckConstraint,
    func,
    text,
    BigInteger,
)

from core.models import Users


class TypeMessage(enum.Enum):
    system = "system"
    bot = "bot"
    operator = "operator"
    client = "client"
    media = "media"


class WebsocketMessageHistory(Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),  # ← PostgreSQL UUID тип
        primary_key=True,
        default=uuid.uuid4,  # ← генерируется автоматически
        server_default=text("gen_random_uuid()"),  # ← для БД
    )
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    file_url: Mapped[str] = mapped_column(nullable=True)
    mime_type: Mapped[str] = mapped_column(nullable=True)
    type_message: Mapped[TypeMessage] = mapped_column(
        Enum(TypeMessage, name="type_message"), nullable=False
    )
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    from_user = relationship(
        "Users", foreign_keys=[from_user_id], back_populates="ws_message_from_user"
    )
    to_user = relationship(
        "Users", foreign_keys=[to_user_id], back_populates="ws_message_to_user"
    )
