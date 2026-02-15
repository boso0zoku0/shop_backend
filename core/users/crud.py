from fastapi import Depends
from sqlalchemy import select, join, outerjoin, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from core import db_helper
from core.auth.crud import get_user_by_cookie
from core.models import GamesUserLiked, Users
from core.schemas.users import UserInfo


async def all_info_about_user(
    user_id: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
):

    stmt = (
        select(
            Users.username,
            Users.date_registration,
            Users.privilege,
            Users.cookie_privileged,
            Users.cookie_privileged_expires,
            GamesUserLiked.game,
        )
        .join(GamesUserLiked, Users.id == GamesUserLiked.user_id)
        .where(Users.id == user_id)
    )
    res = await session.execute(stmt)
    data = res.mappings().first()

    return UserInfo(
        username=data["username"],
        date_registration=data["date_registration"],
        privilege=data["privilege"] or None,
        cookie_privileged=data["cookie_privileged"] or None,
        cookie_privileged_expires=data["cookie_privileged_expires"] or None,
        game=data["game"] or None,
    )


async def info_about_user(
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
    ).where(ranked_users.c.username == current_user["username"])

    result = await session.execute(stmt)
    data = result.first()

    return {
        "username": data.username,
        "date_registration": data.date_registration,
        "total_users": data.total_users,
        "registration_order": data.registration_order,
        "message": f"Among {data.total_users} users, you were #{data.registration_order} to register.",
    }
