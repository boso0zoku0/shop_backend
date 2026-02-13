from fastapi import Depends
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


async def get_genres(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = select(
        Games.genre,
        func.jsonb_array_element_text(Games.gallery, 0).label("first_photo"),
    ).distinct(Games.genre)

    res = await session.execute(stmt)

    return [{"genre": row.genre, "photo": row.first_photo} for row in res]


async def check_users(
    session: AsyncSession = Depends(db_helper.session_dependency),
):

    stmt = select(Users).order_by(asc(Users.id))
    res = await session.execute(stmt)
    users = res.scalars().all()
    return users


async def my_account(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = (
        select(
            Users.username,
            Users.date_registration,
            # func.array_agg(GamesUserRatings.game).label("games"), - вернет список игр(если есть для юзера). но с этим методом надо в return проверять на null. в coalesce это решается на месте
            func.coalesce(func.array_agg(GamesUserLiked.game), []).label("games"),
        )
        .outerjoin(GamesUserLiked, Users.id == GamesUserLiked.user_id)
        .where(Users.id == 14)
        .group_by(Users.id, Users.username, Users.date_registration)
    )
    res = await session.execute(stmt)
    result = res.first()

    if result:
        return {
            "username": result.username,
            "date_registration": result.date_registration,
            "games": result.games if result.games[0] is not None else [],
        }


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
