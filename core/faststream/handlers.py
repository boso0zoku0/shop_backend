import asyncio

from core.websockets import manager
from core.faststream.broker import (
    broker,
    queue_operators,
    queue_clients,
    queue_notify_client,
    exchange,
)


@broker.subscriber(queue=queue_notify_client, exchange=exchange)
async def handler_notifying_client(msg: dict):
    if msg["type"] == "advertising":
        await manager.advertising_to_client(
            client=msg["client"], message=msg["message"]
        )


@broker.subscriber(queue=queue_clients, exchange=exchange)
async def handler_from_client_to_operator(
    msg: dict | str | bytes,
):
    if "file_url" in msg:
        await manager.send_media_to_operator(
            client=msg["from"],
            operator=msg["to"],
            message=msg["message"],
            mime_type=msg["mime_type"],
            file_url=msg["file_url"],
        )
    elif "message" in msg:
        await manager.send_to_operator(
            client=msg["from"],
            operator=msg["to"],
            message=msg["message"],
        )


@broker.subscriber(queue=queue_operators, exchange=exchange)
async def handler_from_operator_to_client(msg: dict):
    if "file_url" in msg:
        await manager.send_media_to_client(
            operator=msg["from"],
            client=msg["to"],
            message=msg["message"],
            mime_type=msg["mime_type"],
            file_url=msg["file_url"],
        )
    elif "message" in msg:
        await manager.send_to_client(
            operator=msg["from"],
            client=msg["to"],
            message=msg["message"],
        )
