from fastapi import APIRouter, Depends, Response, Form, Request, status, HTTPException
from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession


from core import db_helper
from core.auth.crud import (
    login,
    add_user,
    generate_session_id,
    get_user_by_cookie,
    user_statistics,
)
from core.models import Users
from core.models.ws_connections import WebsocketConnections

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/registration", status_code=status.HTTP_201_CREATED)
async def register_user(
    response: Response,
    username: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    cookie = str(generate_session_id())
    response.set_cookie(key="session_id", value=cookie, max_age=604800, path="/")
    await add_user(session=session, username=username, password=password)
    await session.execute(
        update(Users).where(Users.username == username).values(cookie=cookie)
    )
    await session.commit()
    return {"username": username, "password": password, "cookie_session_id": cookie}


@router.post("/login", status_code=status.HTTP_200_OK)
async def user_login(
    response: Response,
    username: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    response_validate = await login(session, username, password)
    if response_validate:

        cookie_update = generate_session_id()
        response.set_cookie(
            key="session_id",
            value=cookie_update,
            max_age=604800,
            path="/",
            secure=False,
        )
        await session.execute(
            update(Users)
            .where(Users.username == username)
            .values(
                cookie=cookie_update,
            )
        )
        await session.commit()
        return {"cookie_session_id": cookie_update}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.get("/user-by-cookie", status_code=status.HTTP_200_OK)
async def cookie_read(
    request: Request, session: AsyncSession = Depends(db_helper.session_dependency)
):
    user_by_cookie = await get_user_by_cookie(request=request, session=session)

    return user_by_cookie


@router.delete("/del", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(session: AsyncSession = Depends(db_helper.session_dependency)):
    await session.execute(delete(WebsocketConnections))
    await session.commit()


@router.delete("/logout", status_code=status.HTTP_200_OK)
async def logout(
    response: Response,
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user_by_cookie = await get_user_by_cookie(
        request=request, session=session, is_logout=True
    )

    await session.delete(user_by_cookie)
    await session.commit()
    response.delete_cookie(key="session_id")
    return "Buy"


@router.get("/users/statistics", status_code=status.HTTP_200_OK)
async def statistics(session: AsyncSession = Depends(db_helper.session_dependency)):
    return await user_statistics(session=session)
