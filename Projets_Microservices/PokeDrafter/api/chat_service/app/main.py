import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.chat import router as chat_router
from app.services import chat_service

logger = logging.getLogger(__name__)


async def kafka_consumer_loop():
    from aiokafka import AIOKafkaConsumer
    retry_delay = 2
    while True:
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        try:
            await consumer.start()
            logger.warning("[Kafka] Consumer connecté sur %s", settings.KAFKA_TOPIC_BATTLE)
            retry_delay = 2
            async for msg in consumer:
                event = msg.value
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
                    logger.warning("[Kafka] Event reçu → broadcast: %s", notif["content"])
                    await chat_service.broadcast_all(notif)
        except asyncio.CancelledError:
            await consumer.stop()
            return
        except Exception as e:
            logger.warning("Kafka indisponible, retry dans %ds : %s", retry_delay, e)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)
        finally:
            try:
                await consumer.stop()
            except Exception:
                pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(kafka_consumer_loop())
    yield
    task.cancel()


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
