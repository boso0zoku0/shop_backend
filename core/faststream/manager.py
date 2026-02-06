from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

from core.websockets import manager

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)
exchange = RabbitExchange("exchange_chat")
queue_clients_greeting = RabbitQueue("greeting_with_clients")
queue_notifying_client_operator = RabbitQueue("notifying_client_operator_connection")
queue_notify_client = RabbitQueue("notify_client")
queue_clients = RabbitQueue("from_clients")
queue_operators = RabbitQueue("from_operators")


@broker.subscriber(
    queue=queue_clients_greeting,
    exchange=exchange,
)
async def handler_greeting_with_clients(
    msg: dict,
):

    await manager.greeting_with_client(msg["client"])


@broker.subscriber(queue=queue_notifying_client_operator, exchange=exchange)
async def handler_notifying_client_operator_connection(msg: dict):

    await manager.notifying_client(client=msg["client"], operator=msg["operator"])


@broker.subscriber(queue=queue_notify_client, exchange=exchange)
async def handler_notifying_client(msg: dict):

    await manager.advertising_to_client(client=msg["client"], message=msg["message"])


@broker.subscriber(queue=queue_clients, exchange=exchange)
async def handler_from_client_to_operator(
    msg: dict | str | bytes,
):

    await manager.send_to_operator(client=msg["client"], message=msg["message"])


@broker.subscriber(queue=queue_operators, exchange=exchange)
async def handler_from_operator_to_client(message: str | dict):

    await manager.send_to_client(
        client=message["client"],
        message=message["message"],
        operator=message["operator"],
    )
