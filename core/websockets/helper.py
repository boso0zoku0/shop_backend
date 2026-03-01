import logging

from click import pass_context
from faststream.asgi import websocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.crud import get_list_games, get_list_genres
from core.faststream.broker import broker, exchange, queue_notify_client
from core.models import PendingMessages
from core.websockets.crud import insert_websocket_db

log = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self):
        self.operators: dict[str, WebSocket] = {}
        self.clients: dict[str, WebSocket] = {}
        # self.active_clients_operators: dict[str, str] = {}  # client - operator

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
        self.clients[client] = websocket
        await self.init_communication_with_client(client)

        if not is_advertising:
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
            await insert_websocket_db(
                session=session,
                username=client,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=is_active,
                connection_type="client",
            )
            stmt = (
                select(PendingMessages)
                .where(PendingMessages.user_id == user_id)
                .limit(1)
            )
            res = await session.execute(stmt)
            message = res.scalar_one_or_none()
            if not message:
                return
            await broker.publish(
                message={
                    "type": "advertising",
                    "client": client,
                    "message": message.message,
                },
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
        # await self.clients[client].send_json(
        #     {"type": "notify", "message": f"Operator {operator} joined the chat"}
        # )
        # log.info(f"✓ Оператор {operator} подключен")

    async def get_clients(self):
        clients: list = []
        for client in self.clients.keys():
            clients.append(client)
        return clients

    async def sender_bot(self, client: str, message: str, session: AsyncSession):

        triggers_operator = {"help me", "call the operator"}
        triggers_bot = {
            "View the movie catalog": lambda: get_list_games(session),
            "View the genre catalog": lambda: get_list_genres(session),
            "Find out the creator of the website": "The creator comes from a small town. The site was created in 2026 as part of a single developer",
            "Call the operator with command - 'help me'": "The operator is already rushing to you",
        }
        # Проверка на вызов оператора
        if any(trigger in message for trigger in triggers_operator):
            await self.clients[client].send_json(
                {
                    "type": "bot_message",
                    "message": "The operator is already rushing to you",
                }
            )
            return True
        # Проверка на остальные команды в боте
        for question, response in triggers_bot.items():
            if question in message:
                if callable(response):
                    answer = await response()
                else:
                    answer = response
                await self.clients[client].send_json(
                    {
                        "type": "bot_message",
                        "message": answer,
                    }
                )
                return True
        return False

    async def init_communication_with_client(self, client: str):
        await self.clients[client].send_json(
            {
                "type": "greeting",
                "message": [
                    f"Hello, {client}, how can I help you?",
                    "1)View the movie catalog",
                    "2) View the genre catalog",
                    "3) Find out the creator of the website",
                    "4) Call the operator with command - 'help me'",
                ],
            }
        )

    async def send_to_operator(self, client: str, operator: str, message: str):
        try:
            await self.operators[operator].send_json(
                {
                    "type": "client_message",
                    "from": client,
                    "to": operator,
                    "message": message,
                }
            )
            log.info(f"Сообщение отправлено оператору: {operator}")
        except Exception as e:
            log.info(f"✗ Ошибка отправки {client} -> ...")

    async def send_to_client(self, client: str, operator: str, message: str):

        try:
            await self.clients[client].send_json(
                {
                    "type": "operator_message",
                    "from": operator,
                    "to": client,
                    "message": message,
                }
            )
            log.info(f"✓ Сообщение отправлено клиенту {client}: {message}")
        except Exception as e:
            log.info(f"✗ Ошибка отправки {operator} -> {client}")

    async def advertising_to_client(self, client: str, message: str):
        await self.clients.get(client).send_json(
            {
                "type": "advertising",
                "to": client,
                "message": message,
            }
        )

    async def send_media_to_client(
        self,
        operator: str,
        client: str,
        file_url: str,
        mime_type: str,
        message: str = "",
    ):
        await self.clients[client].send_json(
            {
                "type": "media",
                "from": operator,
                "to": client,
                "message": message,
                "file_url": file_url,
                "mime_type": mime_type,
            }
        )

    async def send_media_to_operator(
        self,
        client: str,
        operator: str,
        file_url: str,
        mime_type: str,
        message: str = "",
    ):
        await self.operators[operator].send_json(
            {
                "type": "media",
                "from": client,
                "to": operator,
                "message": message,
                "file_url": file_url,
                "mime_type": mime_type,
            }
        )


manager = WebsocketManager()
