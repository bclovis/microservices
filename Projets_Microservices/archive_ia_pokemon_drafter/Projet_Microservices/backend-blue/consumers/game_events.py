"""
Kafka consumer for game events
Listens to duel events from RED team backend
"""
import json
import logging
from kafka import KafkaConsumer
from core.config import settings
from core.kafka import kafka_manager

logger = logging.getLogger(__name__)


def consume_game_events():
    """Consume game events from Kafka"""
    consumer = kafka_manager.create_consumer(
        topic=settings.kafka_topic_duels,
        group_id=f"blue_backend_{settings.kafka_topic_duels}"
    )
    
    logger.info(f"Started consuming game events from topic: {settings.kafka_topic_duels}")
    
    try:
        for message in consumer:
            event = message.value
            logger.info(f"Received game event: {event}")
            
            event_type = event.get("event_type")
            
            if event_type == "duel_created":
                handle_duel_created(event)
            elif event_type == "turn_completed":
                handle_turn_completed(event)
            elif event_type == "duel_completed":
                handle_duel_completed(event)
            elif event_type == "duel_forfeited":
                handle_duel_forfeited(event)
            
    except KeyboardInterrupt:
        logger.info("Stopping game event consumer")
    finally:
        consumer.close()


def handle_duel_created(event: dict):
    """Handle duel created event"""
    logger.info(f"Processing duel created: {event['duel_id']}")
    # TODO: Update local duel state, notify BLUE players


def handle_turn_completed(event: dict):
    """Handle turn completed event"""
    logger.info(f"Processing turn completed for duel: {event['duel_id']}")
    # TODO: Update duel turn state, calculate next turn


def handle_duel_completed(event: dict):
    """Handle duel completed event"""
    logger.info(f"Processing duel completed: {event['duel_id']}")
    # TODO: Update final scores, close duel


def handle_duel_forfeited(event: dict):
    """Handle duel forfeited event"""
    logger.info(f"Processing duel forfeited: {event['duel_id']}")
    # TODO: Update duel status, award points


if __name__ == "__main__":
    from core.logging import setup_logging
    setup_logging()
    consume_game_events()
