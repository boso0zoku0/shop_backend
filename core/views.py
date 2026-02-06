from typing import Literal, Annotated

from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from core import db_helper
from core.auth.crud import get_current_user
from core.crud import (
    games_catalog,
    game_select_genre,
    create_favorite_game,
    sort_date,
    add_rating_for_game,
    get_rating_for_games,
    check_games,
    check_game,
    hidden_games,
    distribution_future,
    get_liked_games,
    user_interactions,
    get_games_preferred,
    create_privilege_level,
)
from core.schemas import GamesBase
from core.schemas.privilege_level import PrivilegeLevel

router = APIRouter(
    prefix="/games",
    tags=["Games"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/to-watch/all", name="genres")
async def watch_games(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await check_games(session=session)


@router.get("/find")
async def find_game(
    game: str = Query(description="Find Game"),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await check_game(game=game, session=session)


@router.get("/to-watch/part")
async def watch_game_catalog(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await games_catalog(session=session)


@router.get("/select-by-genre", name="get_genre")
async def watch_game_catalog(
    genre: Literal["ACTION", "ADVENTURE", "RPG", "STRATEGY", "SIMULATION"] = Query(
        description="Watch genre"
    ),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await game_select_genre(genre=genre, session=session)


@router.post("/add-favorites")
async def add_game_to_favorites(
    request: Request,
    game: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):

    return await create_favorite_game(game, request, session)


@router.get("/sort/by-date")
async def sort_by_date(
    decreasing: bool = Query(
        True,
        description="Sort order: True = descending (newest first), False = ascending (oldest first)",
    ),
    sort_by: Literal["date", "year", "ranking_popularity"] = Query(
        "date",
        description="Sort by: 'date' for full date sorting, 'year' for year-only sorting",
    ),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await sort_date(session=session, sort_by=sort_by, decreasing=decreasing)


@router.post("/vote/rating")
async def post_rating_for_game(
    request: Request,
    game: str = Query(description="Which game should I rate?"),
    rating: int = Query(description="Rating"),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await add_rating_for_game(
        game=game,
        rating=rating,
        session=session,
        request=request,
    )


@router.get("/get/rating")
async def post_rating(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await get_rating_for_games(session=session)


@router.get("/hidden")
async def hidden(
    request: Request,
    selected_games: bool = Query(True, description="Фильтровать выбранные игры"),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await hidden_games(
        request=request, selected_games=selected_games, session=session
    )


@router.get("/future")
async def future_games(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await distribution_future(session=session)


@router.get("/liked")
async def liked_games(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await get_liked_games(request=request, session=session)


@router.get("/watch-to/interactions")
async def user_interactions_with_games(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await user_interactions(request=request, session=session)


@router.get(
    "/preferred",
    # status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def preferred_games(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await get_games_preferred(session=session, request=request)


@router.post(
    "/payment",
)
async def payment_create(
    privilege: PrivilegeLevel,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    response.set_cookie(key="payment", value=privilege.value, max_age=10000)
    await create_privilege_level(privilege=privilege, session=session, request=request)
