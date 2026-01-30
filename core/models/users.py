from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.config import Base
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    func,
    text,
)

from core.schemas.privilege_level import PrivilegeLevel


class Users(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    date_registration: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    cookie: Mapped[str] = mapped_column(nullable=True)
    cookie_expires: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        server_default=text("TIMEZONE('utc', now()) + interval '5 minutes'"),
    )
    access_token: Mapped[str] = mapped_column(nullable=False)
    is_superuser: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    privilege: Mapped[PrivilegeLevel] = mapped_column(
        SQLEnum(PrivilegeLevel, name="privilege_level"),
        nullable=True,
        name="privilege_level",
    )
    cookie_privileged: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    cookie_privileged_expires: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    favorite_genre: Mapped[dict] = mapped_column(
        JSON, nullable=True, default=lambda: {"action": 0, "rpg": 0, "strategy": 0}
    )
    games_user_liked = relationship(
        "GamesUserLiked",
        back_populates="users",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    games_user_ratings = relationship(
        "GamesUserRatings",
        back_populates="users",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # ratings = relationship(
    #     "GamesUserRatings",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True,
    # )
