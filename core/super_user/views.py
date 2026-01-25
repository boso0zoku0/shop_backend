from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import db_helper
from core.super_user.crud import add_game, add_game_characteristic, get_super_user
from core.models import GamesUserLiked
from core.schemas import GamesBase
from core.schemas.games import GamesCharacteristicsPost
from fastapi import APIRouter

router = APIRouter(
    prefix="/superuser/games",
    tags=["SuperUserGames"],
    dependencies=[Depends(get_super_user)],
)


@router.post("/create")
async def create_game(
    game: GamesBase, session: AsyncSession = Depends(db_helper.session_dependency)
):
    return await add_game(session=session, game=game)


@router.post("/create-characteristic")
async def create_game_characteristic(
    characteristic: GamesCharacteristicsPost,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await add_game_characteristic(session=session, characteristic=characteristic)


@router.delete("/remove/liked-games")
async def delete_games(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = select(GamesUserLiked)
    result = await session.execute(stmt)
    games = result.scalars().all()
    for game in games:
        await session.delete(game)
        await session.commit()
