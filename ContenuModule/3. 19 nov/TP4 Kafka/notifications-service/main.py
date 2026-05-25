from kafka import KafkaConsumer
import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

print("Starting notifications service...")

consumer = KafkaConsumer(
    'order.created',
    'inventory.updated',
    'inventory.admin.updated',
    'payment.succeeded',
    'payment.failed',
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='notifications-service'
)

def start_consumer():
    print("Notifications service started...")
    for message in consumer:
        topic = message.topic
        event = message.value
        
        if topic == 'order.created':
            print(f"\nNEW ORDER CREATED:")
            print(f"   Order ID: {event.get('order_id')}")
            print(f"   Product: {event.get('product_id')}")
            print(f"   Quantity: {event.get('quantity')}")
            
        elif topic == 'inventory.updated':
            status = event.get('status')
            if status == 'reserved':
                print(f"\nINVENTORY RESERVED:")
                print(f"   Order ID: {event.get('order_id')}")
                print(f"   Product: {event.get('product_id')}")
                print(f"   Quantity: {event.get('quantity')}")
            else:
                print(f"\nINVENTORY FAILED:")
                print(f"   Order ID: {event.get('order_id')}")
                print(f"   Reason: {event.get('reason')}")
        
        elif topic == 'payment.succeeded':
            print(f"\nPAYMENT SUCCEEDED:")
            print(f"   Order ID: {event.get('order_id')}")
            print(f"   Amount: ${event.get('amount')}")
        
        elif topic == 'payment.failed':
            print(f"\nPAYMENT FAILED:")
            print(f"   Order ID: {event.get('order_id')}")
            print(f"   Reason: {event.get('reason')}")
        
        elif topic == 'inventory.admin.updated':
            print(f"\nADMIN INVENTORY UPDATE:")
            print(f"   Product: {event.get('product_id')}")
            print(f"   Old Quantity: {event.get('old_quantity')}")
            print(f"   New Quantity: {event.get('new_quantity')}")

if __name__ == "__main__":
    start_consumer()
