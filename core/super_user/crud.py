from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core import db_helper
from core.auth.crud import get_user_by_cookie
from core.models import Games, GamesCharacteristics, Users
from core.schemas import GamesBase
from core.schemas.games import GamesCharacteristicsPost


async def add_game(
    game: GamesBase, session: AsyncSession = Depends(db_helper.session_dependency())
) -> set[str]:
    stmt = Games(**game.model_dump())
    print(stmt.release_year)
    session.add(stmt)
    await session.commit()
    return {f"Game: {game.name} - added"}


async def add_game_characteristic(
    characteristic: GamesCharacteristicsPost,
    session: AsyncSession = Depends(db_helper.session_dependency()),
):
    try:
        stmt = GamesCharacteristics(**characteristic.model_dump())
        session.add(stmt)
        await session.commit()

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This characteristic already exists",
        )


async def get_super_user(
    session: Annotated[AsyncSession, Depends(db_helper.session_dependency)],
    request: Request,
):
    current_user = await get_user_by_cookie(request=request, session=session)

    if current_user.is_superuser:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Entry is prohibited."
    )
