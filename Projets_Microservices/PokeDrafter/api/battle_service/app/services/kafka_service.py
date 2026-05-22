import json
import logging
from aiokafka import AIOKafkaProducer
from app.core.config import settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await p.start()
        _producer = p
    return _producer


async def publish_battle_event(event_type: str, data: dict) -> None:
    global _producer
    try:
        producer = await get_producer()
        payload = {"type": event_type, **data}
        await producer.send_and_wait(settings.KAFKA_TOPIC_BATTLE, payload)
    except Exception as exc:
        # Kafka optionnel en dev — on reset le singleton et on log sans crasher
        _producer = None
        logger.warning("Kafka unavailable, event dropped: %s", exc)


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
