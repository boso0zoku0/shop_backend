import secrets
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Form, Request
from sqlalchemy import select, insert, and_, func, update, text
from sqlalchemy.exc import IntegrityError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import count
from starlette import status
from core import db_helper
from core.models import Users
from core.auth import helper


async def get_user_by_cookie(session: AsyncSession, request: Request):
    now = datetime.now(tz=timezone.utc)
    cookie = request.cookies.get("session_id")
    if not cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized"
        )
    stmt = select(Users).where(Users.cookie == cookie)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user.cookie_expires < now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
        )
    return user


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
    stmt = select(Users).where(Users.username == username)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        return False
    hashed_pwd = helper.hash_password(password)
    is_valid = helper.validate_password(password=password, hashed_password=hashed_pwd)
    if is_valid:
        await session.execute(
            update(Users)
            .where(Users.username == username)
            .values(
                cookie_expires=text("TIMEZONE('utc', now()) + interval '5 minutes'")
            )
        )
        await session.commit()
        return True
    return False


async def add_user(
    username: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(db_helper.session_dependency()),
) -> None:
    try:
        stmt = select(Users).where(
            and_(Users.username == username, Users.password == password)
        )
        result = await session.execute(stmt)
        result.scalar()
        hash_password = helper.hash_password(password=password)
        payload = {"username": username, "password": password}
        access_token = helper.encode_jwt(payload=payload)
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
            detail="This user is already registered. Сhange your registration details.",
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


async def get_about_me(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    current_user = await get_user_by_cookie(session, request)

    # CTE с оконными функциями
    ranked_users = select(
        Users.username,
        Users.date_registration,
        func.count().over().label("total_users"),
        func.row_number()
        .over(order_by=[Users.date_registration, Users.id])
        .label("registration_order"),
    ).cte("ranked_users")

    stmt = select(
        ranked_users.c.username,
        ranked_users.c.date_registration,
        ranked_users.c.total_users,
        ranked_users.c.registration_order,
        # CTE создает временную таблицу. Через c. обращаемся к колонке
    ).where(ranked_users.c.username == current_user.username)

    result = await session.execute(stmt)
    data = result.first()

    return {
        "username": data.username,
        "date_registration": data.date_registration,
        "total_users": data.total_users,
        "registration_order": data.registration_order,
        "message": f"Among {data.total_users} users, you were #{data.registration_order} to register.",
    }


def generate_session_id():
    return secrets.token_urlsafe()
