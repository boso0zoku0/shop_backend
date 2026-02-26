from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request

from core import db_helper
from core.auth.crud import get_user_by_cookie
from core.users.crud import info_about_user, all_info_about_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def get_info(
    request: Request, session: AsyncSession = Depends(db_helper.session_dependency)
):
    return await all_info_about_user(request, session=session)


@router.get("/about/me", status_code=status.HTTP_200_OK)
async def about_me(
    request: Request, session: AsyncSession = Depends(db_helper.session_dependency)
):
    return await info_about_user(request=request, session=session)
