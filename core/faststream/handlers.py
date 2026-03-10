import asyncio

from fastapi import Depends

from core import db_helper
from core.websockets import manager
from core.faststream.broker import (
    broker,
    queue_operators,
    queue_clients,
    queue_notify_client,
    exchange,
)


# @broker.subscriber(queue=queue_notify_client, exchange=exchange)
# async def handler_notifying_client(msg: dict):
"""
    Теперь вызываю эту функцию напрямую из websocket manager
"""
#     if msg["type"] == "advertising":
#         await manager.advertising_to_client(
#             client=msg["client"], message=msg["message"]
#         )


@broker.subscriber(queue=queue_clients, exchange=exchange)
async def handler_from_client_to_operator(
    msg: dict | str | bytes,
):
    async with db_helper.session_factory() as session:
        if "file_url" in msg:
            await manager.send_media_to_operator(
                session=session,
                client=msg["from"],
                operator=msg["to"],
                message=msg["message"],
                mime_type=msg["mime_type"],
                file_url=msg["file_url"],
            )
        # if msg["type"] == "disconnect_client":  напрямую из endpoint вызываю, поэтому убрал
        #         #     await manapger.disconnect_client(client=msg["from"])
        else:
            await manager.send_to_operator(
                session=session,  # ← 1. session
                client=msg["from"],  # ← 2. client
                operator=msg["to"],  # ← 3. operator
                message=msg["message"],  # ← 4. message
            )


@broker.subscriber(queue=queue_operators, exchange=exchange)
async def handler_from_operator_to_client(msg: dict):
    async with db_helper.session_factory() as session:
        if "file_url" in msg:
            await manager.send_media_to_client(
                session=session,
                operator=msg["from"],
                client=msg["to"],
                message=msg["message"],
                mime_type=msg["mime_type"],
                file_url=msg["file_url"],
            )
        # if "notify_connect" in msg:
        #     await manager.notify_connect_to_client(
        #         operator=msg["from"], client=msg["to"]
        #     )
        elif "message" in msg:
            await manager.send_to_client(
                session=session,
                operator=msg["from"],
                client=msg["to"],
                message=msg["message"],
            )
