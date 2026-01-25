from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core import db_helper
from core.frontend_db.crud import (
    check_users,
    check_games,
    get_genre_rpg,
    get_genre_action,
    get_genre_strategy,
    get_genres,
    my_account,
    get_rating_for_games2,
    user_vote_ratings,
)
from core.models import GamesUserRatings
from core.schemas import GamesBase

router = APIRouter(tags=["GamesFront"], prefix="/games")


@router.get("/ratings")
async def ratings(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await get_rating_for_games2(session=session)


@router.get("/watch")
async def watch_games(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await check_games(session=session)


@router.get("/watch/genre/rpg")
async def watch_genre(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await get_genre_rpg(session=session)


@router.get("/watch/genre/action")
async def watch_genre(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await get_genre_action(session=session)


@router.get("/watch/genre/strategy")
async def watch_genre(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await get_genre_strategy(session=session)


@router.get("/watch/genres")
async def watch_genres(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await get_genres(session=session)


@router.get("/users-watch")
async def watch_users(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await check_users(session=session)


@router.get("/account")
async def watch_user(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await my_account(session=session)


@router.get("/check_rating")
async def ratings_get(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await user_vote_ratings(session=session)


# @router.get("/check_agregation")
# async def ratings_get(
#     session: AsyncSession = Depends(db_helper.session_dependency),
# ):
#     return await func_agregation(session=session)
