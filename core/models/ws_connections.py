import enum
import datetime as dt
from typing import Optional

from sqlalchemy import func, ForeignKey, String, Integer, DateTime
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


class WebsocketConnections(Base):
    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    connection_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    connected_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    disconnected_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    ip_address: Mapped[str] = mapped_column(
        String(length=50),
        nullable=True,
    )
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("false"),
        nullable=False,
    )
