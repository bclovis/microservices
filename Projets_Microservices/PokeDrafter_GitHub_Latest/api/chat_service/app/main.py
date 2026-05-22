import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routes.chat import router as chat_router
from app.services import chat_service

logger = logging.getLogger(__name__)


async def kafka_consumer_loop():
    from aiokafka import AIOKafkaConsumer
    retry_delay = 2
    while True:
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,
            settings.KAFKA_TOPIC_CHAT,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        try:
            await consumer.start()
            logger.info("[Kafka] Consumer connected to %s and %s", settings.KAFKA_TOPIC_BATTLE, settings.KAFKA_TOPIC_CHAT)
            retry_delay = 2
            async for msg in consumer:
                event = msg.value
                topic = msg.topic
                
                if topic == settings.KAFKA_TOPIC_BATTLE:
                    etype = event.get("type", "")
                    if etype == "turn_played":
                        result = event.get("result", "?")
                        turn = event.get("turn_number", "?")
                        winner = "Rouge" if result == "A" else ("Bleu" if result == "B" else "Egalité")
                        notif = {
                            "author": "bot",
                            "content": f"Tour {turn} — {winner} remporte le tour !",
                            "is_bot": True
                        }
                        logger.info("[Kafka] Battle Event -> broadcast_all")
                        await chat_service.broadcast_all(notif)
                
                elif topic == settings.KAFKA_TOPIC_CHAT:
                    # For chat messages, we broadcast them to everyone (Battle Log)
                    # Or to specific rooms if encoded in the message
                    room = event.get("room")
                    if room:
                        await chat_service.broadcast(room, event)
                    else:
                        # Global broadcast for the "Battle Log" dashboard chat
                        await chat_service.broadcast_all(event)

        except asyncio.CancelledError:
            await consumer.stop()
            return
        except Exception as e:
            logger.warning("Kafka unavailable, retrying in %ds : %s", retry_delay, e)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)
        finally:
            try:
                await consumer.stop()
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Start Kafka consumer
    task = asyncio.create_task(kafka_consumer_loop())
    yield
    # Cleanup
    task.cancel()
    await chat_service.stop_producer()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "chat"}
