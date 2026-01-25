from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
)
from pydantic import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from datetime import datetime, timezone

from core import db_helper
from core.websockets import manager
from core.models import WebsocketsConnections

router = APIRouter()


@router.websocket("/operator")
async def operator_ws(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    if origin is None and origin != "http://localhost:5173":
        await websocket.close(code=1008)
        return

    await websocket.accept()
    manager.operator = websocket

    try:
        while True:
            data = await websocket.receive_json()
            target_client_id = data.get("target_client_id")
            message = data.get("message")

            if target_client_id and message:
                await manager.send_to_clients(
                    client_id=target_client_id, message=message
                )

    except WebSocketDisconnect:
        manager.operator = None
    except json.JSONDecodeError:
        print("Невалидный JSON")
    except Exception as e:
        print(f"Ошибка оператора: {e}")


@router.websocket("/clients/{client_id}")
async def clients_ws(
    websocket: WebSocket,
    client_id: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    headers = dict(websocket.scope.get("headers", []))
    user_agent = headers.get(b"user-agent", b"").decode()
    await manager.connect_client(
        session=session,
        websocket=websocket,
        client_id=client_id,
        ip_address=websocket.client.host if websocket.client else "0.0.0.0",
        user_agent=user_agent,
        is_active=True,
    )
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_to_operator(client_id, data)

    except WebSocketDisconnect:
        await session.execute(
            update(WebsocketsConnections)
            .where(WebsocketsConnections.username == client_id)
            .values(is_active=False, disconnected_at=datetime.now(tz=timezone.utc))
        )
        await session.commit()
        del manager.clients[client_id]
