import enum
from datetime import datetime, timezone
from typing import Sequence, Literal

from fastapi import Depends, HTTPException, status, Request
from fastapi import Query
from sqlalchemy import (
    select,
    asc,
    func,
    desc,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import user

from core import db_helper
from core.models import (
    Games,
    Users,
    GamesUserRatings,
    GamesUserLiked,
)
from core.schemas.users import UsersGet


async def check_games(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = select(Games).order_by(asc(Games.id))
    res = await session.execute(stmt)
    games = res.scalars().all()
    return games


async def get_genre_rpg(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = select(Games).order_by(asc(Games.id)).where(Games.genre == "RPG")
    res = await session.execute(stmt)
    games = res.scalars().all()
    return games


async def get_genre_strategy(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = select(Games).order_by(asc(Games.id)).where(Games.genre == "STRATEGY")
    res = await session.execute(stmt)
    games = res.scalars().all()
    return games


async def get_genre_action(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = select(Games).order_by(asc(Games.id)).where(Games.genre == "ACTION")
    res = await session.execute(stmt)
    games = res.scalars().all()
    return games


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


async def get_rating_for_games2(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt_sub = (
        select(
            GamesUserRatings.game,
            func.sum(GamesUserRatings.rating).label("total_ratings"),
            func.count(GamesUserRatings.rating).label("rating_count"),
        )
        .group_by(GamesUserRatings.game)  # ← group_by НА select!
        .subquery()
    )

    stmt = select(
        stmt_sub.c.game,
        (stmt_sub.c.total_ratings / stmt_sub.c.rating_count).label("average_rating"),
    ).order_by(desc(stmt_sub.c.total_ratings))
    result = await session.execute(stmt)
    data = result.all()

    return [
        {
            "game": game,
            "average_rating": float(average_rating) if average_rating else None,
        }
        for game, average_rating in data
    ]


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
