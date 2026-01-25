from sqlalchemy import func, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from core.config import Base
from sqlalchemy.dialects.postgresql import TIMESTAMP
from core.models import Games, Users


class GamesUserRatings(Base):

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    game: Mapped[str] = mapped_column(
        ForeignKey("games.name", ondelete="CASCADE"),
        primary_key=True,
    )

    # user = relationship(
    #     "Users",
    #     back_populates="ratings",
    # )

    rating: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("rating >= 0 AND rating <= 5"),
        nullable=False,
    )

    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    games = relationship("Games", back_populates="games_user_ratings")

    users = relationship("Users", back_populates="games_user_ratings")
