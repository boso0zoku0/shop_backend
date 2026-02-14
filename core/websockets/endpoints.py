from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    WebSocketException,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from datetime import datetime, timezone
from core import db_helper
from core.models import WebsocketsConnections
from core.websockets import manager
import logging
from core.websockets.crud import get_user_from_cookies
from faststream.rabbit import RabbitExchange, RabbitQueue
from core.faststream.broker import (
    broker,
    exchange,
    queue_operators,
    queue_clients,
    queue_notify_client,
)

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/get-clients")
async def clients():
    if manager.clients:
        return list(manager.clients.keys())
    return []


@router.websocket("/operator/{operator}")
async def operator_ws(
    websocket: WebSocket,
    operator: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    await websocket.accept()
    user = await get_user_from_cookies(websocket, session)
    await manager.connect_operator(
        session=session,
        websocket=websocket,
        operator=operator,
        user_id=user["id"],
        ip_address=user["ip"],
        user_agent=user["user_agent"],
        is_active=True,
    )

    try:
        while True:
            data: dict = await websocket.receive_json()
            print("endpoint websocket")
            print(data)
            log.info(f"Оператор отправил: {data}")
            await broker.publish(
                message={
                    "from": operator,
                    "to": data["to"],
                    "message": data["message"],
                },
                queue=queue_operators,
                exchange=exchange,
            )

    except WebSocketDisconnect:
        if operator in manager.operators:
            await session.execute(
                update(WebsocketsConnections)
                .where(WebsocketsConnections.username == operator)
                .values(is_active=False, disconnected_at=datetime.now(tz=timezone.utc))
            )
            await session.commit()
            del manager.operators[operator]
        log.info("✗ Оператор отключился")
    except Exception as e:
        log.info(f"Ошибка: {e}")


@router.websocket("/clients/{client}")
async def clients_ws(
    websocket: WebSocket,
    client: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    await websocket.accept()
    user = await get_user_from_cookies(websocket, session)

    await manager.connect_client(
        session=session,
        websocket=websocket,
        user_id=user["id"],
        client=client,
        ip_address=user["ip"],
        user_agent=user["user_agent"],
        is_active=True,
        is_advertising=True,
    )
    log.info(f"Клиент {client} подключился")
    try:
        while True:
            data = await websocket.receive_json()

            handler_bot = await manager.sender_bot(
                client=client, message=data["message"], session=session
            )
            if not handler_bot and "to" in data:
                log.info(f"data: {data['from']} ; {data['message']}")
                await broker.publish(
                    message={
                        "from": data["from"],
                        "to": data["to"],
                        "message": data["message"],
                    },
                    queue=queue_clients,
                    exchange=exchange,
                )
            elif not handler_bot:
                log.info("Кликает по ответу бота")

    except WebSocketDisconnect:
        await session.execute(
            update(WebsocketsConnections)
            .where(WebsocketsConnections.username == client)
            .values(is_active=False, disconnected_at=datetime.now(tz=timezone.utc))
        )
        await session.commit()
        del manager.clients[client]
