"""
Kafka producer and consumer utilities
"""
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import logging
from typing import Dict, Any, Optional
from .config import settings

logger = logging.getLogger(__name__)


class KafkaManager:
    """Manages Kafka producer and consumer instances"""
    
    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
        self.consumers: Dict[str, KafkaConsumer] = {}
    
    def get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer instance"""
        if self.producer is None:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=settings.kafka_broker,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None
                )
                logger.info(f"Kafka producer connected to {settings.kafka_broker}")
            except KafkaError as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                raise
        
        return self.producer
    
    def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None) -> None:
        """Send a message to a Kafka topic"""
        try:
            producer = self.get_producer()
            future = producer.send(topic, value=message, key=key)
            future.get(timeout=10)  # Wait for confirmation
            logger.info(f"Message sent to topic '{topic}': {message}")
        except KafkaError as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            raise
    
    def create_consumer(self, topic: str, group_id: str) -> KafkaConsumer:
        """Create a Kafka consumer for a specific topic"""
        consumer_key = f"{topic}_{group_id}"
        
        if consumer_key not in self.consumers:
            try:
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=settings.kafka_broker,
                    group_id=group_id,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='latest',
                    enable_auto_commit=True
                )
                self.consumers[consumer_key] = consumer
                logger.info(f"Kafka consumer created for topic '{topic}' with group '{group_id}'")
            except KafkaError as e:
                logger.error(f"Failed to create Kafka consumer: {e}")
                raise
        
        return self.consumers[consumer_key]
    
    def close(self):
        """Close all Kafka connections"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")
        
        for consumer in self.consumers.values():
            consumer.close()
        
        self.consumers.clear()
        logger.info("All Kafka consumers closed")


# Global Kafka manager instance
kafka_manager = KafkaManager()


# Helper functions
def send_duel_event(event_type: str, duel_id: int, data: Dict[str, Any]) -> None:
    """Send a duel-related event to Kafka"""
    message = {
        "event_type": event_type,
        "duel_id": duel_id,
        "timestamp": str(datetime.now()),
        "team": settings.team_color,
        "data": data
    }
    kafka_manager.send_message(settings.kafka_topic_duels, message, key=str(duel_id))


def send_chat_message(user_id: int, username: str, message: str, team_only: bool = False) -> None:
    """Send a chat message to Kafka"""
    msg = {
        "user_id": user_id,
        "username": username,
        "message": message,
        "team": settings.team_color,
        "team_only": team_only,
        "timestamp": str(datetime.now())
    }
    kafka_manager.send_message(settings.kafka_topic_chat, msg, key=str(user_id))


def send_notification(user_id: int, notification_type: str, data: Dict[str, Any]) -> None:
    """Send a notification to Kafka"""
    message = {
        "user_id": user_id,
        "notification_type": notification_type,
        "timestamp": str(datetime.now()),
        "data": data
    }
    kafka_manager.send_message(settings.kafka_topic_notifications, message, key=str(user_id))
