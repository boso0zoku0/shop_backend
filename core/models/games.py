import enum
from datetime import datetime

from sqlalchemy import func, ForeignKey
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


class GameGenre(enum.Enum):
    ACTION = "action"
    ADVENTURE = "adventure"
    RPG = "rpg"
    STRATEGY = "strategy"
    SIMULATION = "simulation"


class Games(Base):
    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(
        Text,
        # №1 можно тут, но только в виде строчки, так как колонки ещё нет
        CheckConstraint("length(name) <= 100"),
        nullable=False,
        unique=True,
        name="name",
    )
    release_year: Mapped[str] = mapped_column(nullable=True)
    genre: Mapped[GameGenre] = mapped_column(
        nullable=False, default=GameGenre.ADVENTURE
    )
    story: Mapped[str] = mapped_column(Text, nullable=False)
    gameplay: Mapped[str] = mapped_column(Text, nullable=False)
    graphics: Mapped[str] = mapped_column(Text, nullable=True)
    game_development: Mapped[str] = mapped_column(Text, nullable=True)
    gallery: Mapped[list[str]] = mapped_column(JSONB, nullable=True)

    system_requirements = relationship("GamesCharacteristics", back_populates="game")

    games_user_liked = relationship(
        "GamesUserLiked",
        back_populates="games",
        passive_deletes=True,
        cascade="all, delete",
    )

    games_user_ratings = relationship(
        "GamesUserRatings",
        back_populates="games",
    )

    @hybrid_property
    def release_date_converted(self):
        """Внутреннее свойство для преобразования строки в объект даты"""
        if not self.release_year:
            return None

        formats = ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d.%m.%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(self.release_year, fmt).date()
            except ValueError:
                continue
        return None

    @hybrid_property
    def is_future(self) -> bool:
        """Это поле увидит Pydantic"""
        rd = self.release_date_converted
        return rd > datetime.now().date() if rd else False

    @is_future.expression
    def is_future(cls):
        """Это поле будет использовать эндпоинт в .where(Games.is_future == True)"""
        # to_date в Postgres отлично справляется с "May 13, 2016"
        return func.to_date(cls.release_year, "Month DD, YYYY") > func.current_date()
