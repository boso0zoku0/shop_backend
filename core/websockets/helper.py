import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.faststream.manager import broker, exchange, queue_notify_client
from core.models import PendingMessages
from core.websockets.crud import insert_websocket_db
from datetime import datetime

log = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self):
        self.operators: dict[str, WebSocket] = {}
        self.clients: dict[str, WebSocket] = {}

    async def connect_client(
        self,
        websocket: WebSocket,
        client: str,
        ip_address: str,
        user_agent: str,
        is_active: bool,
        user_id: int,
        session: AsyncSession,
        is_advertising: bool = False,
    ):
        if not is_advertising:
            self.clients[client] = websocket
            await insert_websocket_db(
                session=session,
                username=client,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=is_active,
                connection_type="client",
            )
        else:
            self.clients[client] = websocket
            await insert_websocket_db(
                session=session,
                username=client,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=is_active,
                connection_type="client",
            )
            stmt = select(PendingMessages).where(PendingMessages.user_id == user_id)
            res = await session.execute(stmt)
            message = res.scalar_one_or_none()
            if not message:
                return
            await broker.publish(
                message={"client": client, "message": message.message},
                queue=queue_notify_client,
                exchange=exchange,
            )
            await session.delete(message)

    async def connect_operator(
        self,
        websocket: WebSocket,
        operator: str,
        user_id: int,
        ip_address: str,
        user_agent: str,
        is_active: bool,
        session: AsyncSession,
    ):
        self.operators[operator] = websocket
        await insert_websocket_db(
            session=session,
            username=operator,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=is_active,
            connection_type="operator",
        )
        log.info(f"✓ Оператор {operator} подключен")

    async def greeting_with_client(self, client: str):
        await self.clients[client].send_text(f"Hello, {client}, how can I help you?")

    async def notifying_client(self, client: str, operator: str):
        await self.clients[client].send_text(f"Operator {operator} joined the chat")

    async def send_to_operator(self, client: str, message: str):
        """Отправка сообщения оператору"""
        if not self.operators:
            log.info("✗ Нет подключенных операторов")
            return

        for operator_id, operator_ws in self.operators.items():
            try:
                await operator_ws.send_json(
                    {
                        "type": "client_message",
                        # "action": "connected",
                        "client_id": client,
                        "message": message,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                log.info(
                    f"✓ Сообщение от {client} отправлено оператору {operator_id}: {message}"
                )
                log.info(f"OP_ID:{operator_id} WS: {operator_ws}")
            except Exception as e:
                log.info(f"✗ Ошибка отправки оператору {operator_id}: {e}")

    async def send_to_client(self, client: str, message: str | dict, operator: str):
        """Отправка сообщения клиенту"""
        try:
            await self.clients[client].send_text(
                message
            )  # Сообщения от оператора клиенту теперь как строка, а не json
            log.info(f"✓ Сообщение отправлено клиенту {client}: {message}")
        except Exception as e:
            log.info(f"✗ Ошибка отправки клиенту {client}: {e}")

    async def notify_operator_client_connected(self, client: str):
        """Уведомление оператора о новом подключении клиента"""
        for operator_id, operator_ws in self.operators.items():
            try:
                await operator_ws.send_json(
                    {
                        "type": "notify_to_connection",
                        "client_id": client,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except WebSocketDisconnect as e:
                log.warning(e)

    async def advertising_to_client(self, client: str, message: str):
        await self.clients[client].send_text(message)


manager = WebsocketManager()
