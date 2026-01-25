from sqlalchemy import func, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.config import Base
from core.models import Games
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


class GamesCharacteristics(Base):
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), primary_key=True)
    game = relationship("Games", back_populates="system_requirements")
    oc: Mapped[str] = mapped_column(Text, nullable=False)
    cpu: Mapped[str] = mapped_column(Text, nullable=False)
    gpu: Mapped[str] = mapped_column(Text, nullable=False)
    ram: Mapped[str] = mapped_column(Text, nullable=False)
    disk_space: Mapped[str] = mapped_column(Text, nullable=False)
