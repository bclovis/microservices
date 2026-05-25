from kafka import KafkaConsumer, KafkaProducer
import json
import os
import random

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

print("Starting payment service...")

consumer = KafkaConsumer(
    'inventory.updated',
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='payment-service'
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def process_inventory_update(event):
    order_id = event['order_id']
    status = event.get('status')
    
    if status != 'reserved':
        print(f"Order {order_id} was not reserved, skipping payment")
        return
    
    # Simule un paiement (70% de succès)
    success = random.random() > 0.3
    
    if success:
        payment_event = {
            "order_id": order_id,
            "status": "succeeded",
            "amount": event['quantity'] * 10.0
        }
        producer.send('payment.succeeded', payment_event)
        print(f"Payment succeeded for order {order_id}")
    else:
        payment_event = {
            "order_id": order_id,
            "status": "failed",
            "reason": "card declined"
        }
        producer.send('payment.failed', payment_event)
        print(f"Payment failed for order {order_id}")
    
    producer.flush()

def start_consumer():
    print("Payment service started, waiting for inventory updates...")
    for message in consumer:
        event = message.value
        process_inventory_update(event)

if __name__ == "__main__":
    start_consumer()
