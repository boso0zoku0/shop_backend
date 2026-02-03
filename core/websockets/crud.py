import json
from typing import Optional

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import WebSocket

from core.models import Users
from core.models.ws_connections import WebsocketConnections


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


async def get_user_from_cookies(
    websocket: WebSocket, session: AsyncSession
) -> Optional[Users]:

    headers = dict(websocket.scope.get("headers", []))
    cookie_header = headers.get(b"session_id", b"").decode()

    cookies = {}
    for cookie in cookie_header.split(";"):
        if "=" in cookie:
            key, value = cookie.strip().split("=", 1)
            cookies[key] = value

    session_id = cookies.get("session_id")

    if not session_id:
        return None

    stmt = select(Users).where(Users.cookie == session_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    return user  # ← User со ВСЕМИ данными (id, username, role...)


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
