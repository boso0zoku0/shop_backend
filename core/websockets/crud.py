from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.ws_connections import WebsocketConnections


async def insert_websocket_db(
    session: AsyncSession,
    username: str,
    ip_address: str,
    user_agent: str,
    is_active: bool,
    connection_type: str,
):
    stmt = insert(WebsocketConnections).values(
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        is_active=is_active,
        connection_type=connection_type,
    )
    await session.execute(stmt)
    await session.commit()
