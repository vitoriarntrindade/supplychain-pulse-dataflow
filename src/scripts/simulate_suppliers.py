"""Producer de eventos para Kafka."""

import asyncio
import json
import os
import random
from typing import Any

from aiokafka import AIOKafkaProducer
from scripts.factories import (
    OrderCreatedFactory,
    OrderDelayedFactory,
    InventoryLowFactory,
)

TOPIC: str = os.getenv("KAFKA_TOPIC", "supplychain_events")
KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

FACTORIES: list[Any] = [
    OrderCreatedFactory,
    OrderDelayedFactory,
    InventoryLowFactory,
]


async def produce_events() -> None:
    """
    Produz eventos para o Kafka usando subfactories do Factory Boy.

    Os eventos são gerados aleatoriamente e enviados para o tópico
    definido em `KAFKA_TOPIC`.
    """
    producer: AIOKafkaProducer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP
    )
    await producer.start()
    try:
        while True:
            factory_cls = random.choice(FACTORIES)
            event = factory_cls()
            msg: bytes = json.dumps(event).encode("utf-8")
            await producer.send_and_wait(TOPIC, msg)
            print(f"[PRODUCER] Sent: {event}")
            await asyncio.sleep(random.uniform(1, 3))
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(produce_events())
