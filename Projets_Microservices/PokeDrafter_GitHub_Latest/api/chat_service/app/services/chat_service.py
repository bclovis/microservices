import json
from collections import defaultdict
from typing import Dict, List
from fastapi import WebSocket
import logging
from aiokafka import AIOKafkaProducer
from sqlalchemy import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.message import Message

logger = logging.getLogger(__name__)

# Connections grouped by room (team or battle_id)
_connections: Dict[str, List[WebSocket]] = defaultdict(list)
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


async def connect(room: str, ws: WebSocket):
    await ws.accept()
    _connections[room].append(ws)
    logger.info(f"WebSocket accepted for room: {room}. Total in room: {len(_connections[room])}")


def disconnect(room: str, ws: WebSocket):
    try:
        if ws in _connections[room]:
            _connections[room].remove(ws)
            logger.info(f"WebSocket removed from room: {room}. Remaining in room: {len(_connections[room])}")
    except Exception as e:
        logger.error(f"Error during disconnect: {e}")


async def publish_message(message: dict):
    """Publish a message to Kafka and save it to the database."""
    # Save to database
    try:
        async with AsyncSessionLocal() as db:
            db_msg = Message(
                room=message.get("room"),
                author=message.get("author"),
                content=message.get("content"),
                is_bot=message.get("is_bot", False),
                team=message.get("team")
            )
            db.add(db_msg)
            await db.commit()
    except Exception as e:
        logger.error(f"Error saving message to DB: {e}")

    # Publish to Kafka
    try:
        producer = await get_producer()
        await producer.send_and_wait(settings.KAFKA_TOPIC_CHAT, message)
    except Exception as e:
        logger.warning(f"Kafka producer error: {e}")


async def broadcast(room: str, message: dict):
    """Broadcast a message to local connections in a specific room."""
    if room not in _connections:
        return
    
    dead = []
    for ws in list(_connections[room]):
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send message to a client in {room}, marking as dead: {e}")
            dead.append(ws)
            
    for ws in dead:
        disconnect(room, ws)


async def broadcast_all(message: dict):
    """Broadcast a message to all connected clients in red and blue teams."""
    logger.info(f"Broadcasting to all teams: {message.get('content')}")
    for team in ["red", "blue"]:
        await broadcast(team, message)


async def get_history(limit: int = 50) -> List[dict]:
    """Get the latest chat messages from the database."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Message).order_by(Message.sent_at.desc()).limit(limit)
        )
        messages = result.scalars().all()
        # Return in chronological order
        return [
            {
                "author": m.author,
                "content": m.content,
                "is_bot": m.is_bot,
                "team": m.team,
                "sent_at": m.sent_at.isoformat() if m.sent_at else None
            }
            for m in reversed(messages)
        ]


async def stop_producer():
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
