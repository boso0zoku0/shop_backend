import secrets
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Form
from sqlalchemy import select, insert, and_, func, update, text
from sqlalchemy.exc import IntegrityError

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request

from core import db_helper
from core.models import Users, PendingMessages
from core.auth import helper
from core.models.ws_connections import WebsocketConnections
from core.schemas.privilege_level import PrivilegeLevel


async def advertising_offer_to_client(
    session: AsyncSession,
    client: str,
):

    now = datetime.now(tz=timezone.utc)
    time_up = timedelta(days=7)
    expires_time = now - time_up
    operators = ["bob", "john"]
    stmt = (
        select(
            func.count(WebsocketConnections.connected_at),
        )
        .join(Users, WebsocketConnections.user_id == Users.id)
        .where(
            and_(
                Users.username == client,
                Users.username != "bob",
                WebsocketConnections.connected_at >= expires_time,
            )
        )
        .group_by(WebsocketConnections.username)
    )
    res = await session.scalar(stmt)
    if res is None:
        return False
    if res >= 3:
        return True
    return False


async def get_user_by_cookie(
    session: AsyncSession, request: Request, is_logout: bool | None = False
):
    now = datetime.now(tz=timezone.utc)
    cookie = request.cookies.get("session_id")
    if not cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized"
        )
    stmt = select(Users).where(Users.cookie == cookie)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized"
        )
    if user.cookie_expires < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
        )
    if is_logout:
        return user
    return {"username": user.username, "user_id": user.id}


async def get_current_user(
    session: Annotated[AsyncSession, Depends(db_helper.session_dependency)],
    request: Request,
):
    user_by_cookie = await get_user_by_cookie(session, request)

    return user_by_cookie


async def login(
    session: Annotated[AsyncSession, Depends(db_helper.session_dependency)],
    username: str = Form(),
    password: str = Form(),
):
    user = (
        await session.scalars(select(Users).where(Users.username == username))
    ).first()

    if not user:
        return False
    hashed_pwd = helper.hash_password(password)
    is_valid = helper.validate_password(password=password, hashed_password=hashed_pwd)
    is_offer = await advertising_offer_to_client(session, username)
    if is_valid:

        if is_offer:
            await session.execute(
                update(Users)
                .where(Users.username == username)
                .values(
                    cookie_expires=text(
                        "TIMEZONE('utc', now()) + interval '10800 minutes'"
                    )
                )
            )
            pending_msg = PendingMessages(
                user_id=user.id,
                message="Subscribe to our newsletter to receive exclusive offers.",
                is_read=False,
            )
            session.add(pending_msg)

            await session.commit()

        await session.execute(
            update(Users)
            .where(Users.username == username)
            .values(
                cookie_expires=text("TIMEZONE('utc', now()) + interval '10800 minutes'")
            )
        )
        return True

    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def add_user(
    username: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(db_helper.session_dependency()),
) -> None:
    try:
        hash_password = helper.hash_password(password=password)
        access_token = helper.encode_jwt(
            payload={"sub": username, "username": username}
        )
        stmt = insert(Users).values(
            username=username,
            password=str(hash_password),
            access_token=access_token,
        )

        await session.execute(stmt)
        await session.commit()

    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user is already registered. Change your registration details.",
        )


""" 24-hour statistics """


async def user_statistics(
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    time_threshold = datetime.now(tz=timezone.utc) - timedelta(hours=24)
    stmt = select(func.count(Users.username)).where(
        Users.date_registration > time_threshold
    )
    res = await session.execute(stmt)
    users_count = res.scalar()
    return users_count or 0


def generate_session_id():
    return secrets.token_urlsafe()


async def create_privilege_level(
    privilege: PrivilegeLevel,
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(session, request)
    expire_cookie: int = 0
    if privilege.value == "weak":
        expire_cookie = 20
    if privilege.value == "medium":
        expire_cookie = 2000
    if privilege.value == "best":
        expire_cookie = 10000
    await session.execute(
        update(Users)
        .where(Users.username == user.get("username"))
        .values(
            privilege=privilege,
            cookie_privileged=func.now(),
            cookie_privileged_expires=text(
                f"TIMEZONE('utc', now()) + interval '{expire_cookie} minutes'"
            ),
        )
    )
    await session.commit()
