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

    await manager.send_to_operator(client=msg["client"], message=msg["message"])


@broker.subscriber(queue=queue_operators, exchange=exchange)
async def handler_from_operator_to_client(message: dict):

    await manager.send_to_client(
        client=message["client"],
        message=message["message"],
        operator=message["operator"],
    )
