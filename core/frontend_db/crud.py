from fastapi import Depends, Request
from sqlalchemy import (
    select,
    asc,
    func,
    desc,
)
from sqlalchemy.ext.asyncio import AsyncSession

from core import db_helper
from core.models import (
    Games,
    Users,
    GamesUserRatings,
    GamesUserLiked,
)


async def check_users(
    session: AsyncSession = Depends(db_helper.session_dependency),
):

    stmt = select(Users).order_by(asc(Users.id))
    res = await session.execute(stmt)
    users = res.scalars().all()
    return users


async def user_vote_ratings(
    session: AsyncSession = Depends(db_helper.session_dependency),
):

    stmt = (
        select(
            GamesUserRatings.user_id,
            func.array_agg(GamesUserRatings.game).label("total_games"),
            func.array_agg(GamesUserRatings.rating).label("total_ratings"),
        )
        .where(GamesUserRatings.user_id == 5)
        .group_by(GamesUserRatings.user_id)
    )

    res = await session.execute(stmt)
    result = res.first()

    if not result:
        return {"user_id": 5, "total_games": [], "total_ratings": []}

    # Правильный способ распаковки
    user_id, total_games, total_ratings = result

    return {
        "user_id": user_id,
        "total_games": total_games or [],
        "total_ratings": total_ratings or [],
    }
