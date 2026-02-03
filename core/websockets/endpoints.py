from contextlib import asynccontextmanager
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    WebSocketException,
    Query,
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

from core.websockets.helper import broker

log = logging.getLogger(__name__)
router = APIRouter()


exchange = RabbitExchange("exchange_chat")
queue_clients_greeting = RabbitQueue("greeting_with_clients")
queue_clients = RabbitQueue("from_clients")
queue_notifying_client_operator = RabbitQueue("notifying_client_operator_connection")
queue_operators = RabbitQueue("from_operators")


@router.websocket("/operator/{operator}/{client}")
async def operator_ws(
    websocket: WebSocket,
    operator: str,
    client: str,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    await websocket.accept()
    await manager.connect_operator(
        session=session,
        websocket=websocket,
        operator=operator,
        user_id=77,
        ip_address=websocket.client.host if websocket.client else "0.0.0.0",
        user_agent="console",
        is_active=True,
    )
    await broker.publish(
        {"client": client, "operator": operator},
        queue=queue_notifying_client_operator,
        exchange=exchange,
    )

    try:
        while True:
            # Ждем сообщения от оператора (для отправки клиенту)
            data: str = await websocket.receive_text()
            log.info(f"Оператор отправил: {data}")

            await broker.publish(
                message={"client": client, "message": data},
                queue=queue_operators,
                exchange=exchange,
            )

            # if "client_id" in data and "message" in data:
            #     await manager.send_to_client(
            #         client_id=data["client_id"], message=data["message"]
            #     )

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
    # user = await get_user_from_cookies(websocket, session)
    # if user is None:
    #     raise WebSocketException(code=1008)
    # headers = dict(websocket.scope.get("headers", []))
    # user_agent = headers.get(b"user-agent", b"").decode()
    await manager.connect_client(
        session=session,
        websocket=websocket,
        user_id=78,
        client=client,
        ip_address=websocket.client.host if websocket.client else "0.0.0.0",
        user_agent="console",
        is_active=True,
    )
    await broker.publish(
        {"client": client}, queue=queue_clients_greeting, exchange=exchange
    )
    try:
        while True:
            log.info(f"Клиент {client} подключился")
            data = await websocket.receive_text()

            await broker.publish(
                message={"client": client, "message": data},
                queue=queue_clients,
                exchange=exchange,
            )

            # await manager.send_to_operator(client_id, data)

    except WebSocketDisconnect:
        await session.execute(
            update(WebsocketsConnections)
            .where(WebsocketsConnections.username == client)
            .values(is_active=False, disconnected_at=datetime.now(tz=timezone.utc))
        )
        await session.commit()
        del manager.clients[client]


#
# connection_manager = ConnectionManager()
# # RabbitMQ сервис
# rabbitmq = SupportChatRabbitMQ()

# @router.websocket("/ws/client/{client_id}")
# async def client_websocket(websocket: WebSocket, client_id: str):
#     """WebSocket для клиентов (публикуют сообщения)"""
#     await connection_manager.connect_client(client_id, websocket)
#
#     try:
#         while True:
#             # Клиент отправляет сообщение
#             data = await websocket.receive_text()
#             message_data = json.loads(data)
#
#             if message_data.get("type") == "new_request":
#                 # Клиент создает новый запрос в поддержку
#
#                 await websocket.send_text(
#                     json.dumps(
#                         {
#                             "status": "request_sent",
#                             "message": "Запрос отправлен операторам",
#                         }
#                     )
#                 )
#
#             elif message_data.get("type") == "chat_message":
#                 # Сообщение в существующем чате
#                 chat_id = message_data["chat_id"]
#                 await rabbitmq.send_chat_message(
#                     chat_id=chat_id,
#                     sender=f"client_{client_id}",
#                     message=message_data["text"],
#                 )
#
#     except WebSocketDisconnect:
#         await connection_manager.disconnect_client(client_id)
#         print(f"Client {client_id} disconnected")
#
#
# # =================== ОПЕРАТОРЫ ===================
#
#
# @router.websocket("/ws/operator/{operator_id}")
# async def operator_websocket(websocket: WebSocket, operator_id: str):
#     """WebSocket для операторов (потребляют сообщения)"""
#     await connection_manager.connect_operator(operator_id, websocket)
#
#     try:
#         # Запускаем прослушивание новых запросов
#         await rabbitmq.listen_for_requests(operator_id)
#
#         while True:
#             # Оператор может отправлять сообщения клиентам
#             data = await websocket.receive_text()
#             message_data = json.loads(data)
#
#             if message_data.get("type") == "accept_request":
#                 # Оператор принимает запрос от клиента
#                 client_id = message_data["client_id"]
#                 chat_id = await rabbitmq.create_chat_session(
#                     client_id=client_id, operator_id=operator_id
#                 )
#
#                 # Уведомляем клиента
#                 await connection_manager.send_to_client(
#                     client_id,
#                     json.dumps(
#                         {
#                             "type": "operator_assigned",
#                             "operator_id": operator_id,
#                             "chat_id": chat_id,
#                         }
#                     ),
#                 )
#
#                 # Уведомляем оператора
#                 await websocket.send_text(
#                     json.dumps(
#                         {
#                             "type": "chat_created",
#                             "chat_id": chat_id,
#                             "client_id": client_id,
#                         }
#                     )
#                 )
#
#             elif message_data.get("type") == "chat_message":
#                 # Оператор отвечает в чат
#                 chat_id = message_data["chat_id"]
#                 await rabbitmq.send_chat_message(
#                     chat_id=chat_id,
#                     sender=f"operator_{operator_id}",
#                     message=message_data["text"],
#                 )
#
#                 # Отправляем клиенту
#                 client_id = await rabbitmq.get_client_by_chat(chat_id)
#                 await connection_manager.send_to_client(
#                     client_id,
#                     json.dumps(
#                         {
#                             "type": "message",
#                             "chat_id": chat_id,
#                             "text": message_data["text"],
#                             "sender": f"operator_{operator_id}",
#                         }
#                     ),
#                 )
#
#     except WebSocketDisconnect:
#         await connection_manager.disconnect_operator(operator_id)
#         print(f"Operator {operator_id} disconnected")
#
#
# # =================== HTTP ЭНДПОИНТЫ ===================
#
#
# @router.get("/api/chat/requests")
# async def get_pending_requests(operator_id: str):
#     """Получить список ожидающих запросов (для оператора)"""
#     return await rabbitmq.get_pending_requests()
#
#
# @router.post("/api/chat/{chat_id}/close")
# async def close_chat(chat_id: str, operator_id: str):
#     """Закрыть чат (оператор)"""
#     await rabbitmq.close_chat(chat_id)
#     return {"status": "chat_closed", "chat_id": chat_id}
#
#
# @router.get("/api/operator/{operator_id}/stats")
# async def get_operator_stats(operator_id: str):
#     """Статистика оператора"""
#     return await rabbitmq.get_operator_stats(operator_id)
#
#
# # =================== ДОПОЛНИТЕЛЬНЫЕ ===================
#
#
# @router.websocket("/ws/chat/{chat_id}")
# async def chat_websocket(
#     websocket: WebSocket, chat_id: str, user_type: str, user_id: str
# ):
#     """Прямое подключение к очереди чата (альтернатива)"""
#     await websocket.accept()
#
#     # Подписываемся на очередь этого чата
#     async def on_chat_message(msg: str):
#         await websocket.send_text(msg)
#
#     await rabbitmq.subscribe_to_chat(chat_id, on_chat_message)
#
#     try:
#         while True:
#             data = await websocket.receive_text()
#             # Отправляем сообщение в очередь чата
#             await rabbitmq.send_to_chat_queue(chat_id, data)
#     except WebSocketDisconnect:
#         pass
#
#
# @router.get("/health")
# async def health_check():
#     """Проверка здоровья сервиса и RabbitMQ"""
#     is_rabbitmq_ok = await rabbitmq.check_connection()
#     return {
#         "status": "healthy" if is_rabbitmq_ok else "unhealthy",
#         "rabbitmq": "connected" if is_rabbitmq_ok else "disconnected",
#         "timestamp": "2024-01-29T10:00:00",
#     }
