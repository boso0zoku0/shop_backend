import json
from sqlalchemy import insert, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket, WebSocketException
from fastapi import Request, Depends
from core import db_helper
from core.auth.crud import get_user_by_cookie
from core.models import Users
from core.models.ws_connections import WebsocketConnections
from core.models.ws_history_message import WebsocketMessageHistory, TypeMessage


async def get_user_dialog(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    user = await get_user_by_cookie(session=session, request=request)
    stmt = select(WebsocketMessageHistory).where(
        or_(
            WebsocketMessageHistory.to_user_id == user["user_id"],
            WebsocketMessageHistory.from_user_id == user["user_id"],
        )
    )

    result = await session.execute(stmt)
    msg = result.scalars().all()
    return msg


async def insert_websocket_db(
    session: AsyncSession,
    username: str,
    user_id: int,
    ip_address: str,
    user_agent: str,
    is_active: bool,
    connection_type: str,
):
    stmt = insert(WebsocketConnections).values(
        username=username,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=is_active,
        connection_type=connection_type,
    )
    await session.execute(stmt)
    await session.commit()


async def get_user_by_name(
    username: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = select(Users.id).where(Users.username == username)
    result = await session.execute(stmt)
    res = result.scalars().first()
    return res


async def insert_message_history(
    message: str,
    type_message: TypeMessage,
    file_url: str | None = None,
    mime_type: str | None = None,
    from_user_id: int | None = None,
    to_user_id: int | None = None,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    stmt = insert(WebsocketMessageHistory).values(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        message=message,
        type_message=type_message,
        file_url=file_url,
        mime_type=mime_type,
    )
    await session.execute(stmt)
    await session.commit()


async def get_user_from_cookies(websocket: WebSocket, session: AsyncSession):

    headers = dict(websocket.scope.get("headers", []))
    cookie_header = headers.get(b"cookie", b"").decode()

    cookies = {}
    for cookie in cookie_header.split(";"):
        if "=" in cookie:
            key, value = cookie.strip().split("=", 1)
            cookies[key] = value

    session_id = cookies.get("session_id")

    if not session_id:
        raise WebSocketException(code=1008)
    headers = dict(websocket.scope.get("headers", []))
    user_agent = headers.get(b"user-agent", b"").decode()
    ip = websocket.client.host if websocket.client else "0.0.0.0"

    stmt = select(Users).where(Users.cookie == session_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    return {
        "id": user.id,
        "username": user.username,
        "headers": headers,
        "user_agent": user_agent,
        "ip": ip,
    }


async def parse(msg):
    if isinstance(msg, bytes):
        msg_str = msg.decode("utf-8", errors="ignore")

        msg = json.loads(msg_str)

    if isinstance(msg, str):
        try:
            return json.loads(msg)
        except json.JSONDecodeError:
            return {"message": msg, "client": "Anna"}
    else:
        return msg
