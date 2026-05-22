from kafka import KafkaConsumer, KafkaProducer
from database import SessionLocal, Product
import json
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:9092")

print("Starting inventory service...")

consumer = KafkaConsumer(
    'order.created',
    'payment.failed',
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='inventory-service'
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

reservations = {}

def handle_order_created(event):
    db = SessionLocal()
    
    product_id = event['product_id']
    quantity = event['quantity']
    order_id = event['order_id']
    
    product = db.query(Product).filter(Product.product_id == product_id).first()
    
    if product and product.quantity >= quantity:
        product.quantity -= quantity
        db.commit()
        
        reservations[order_id] = {'product_id': product_id, 'quantity': quantity}
        
        inventory_event = {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "status": "reserved"
        }
        producer.send('inventory.updated', inventory_event)
        print(f"Stock reserved: {product_id}, remaining: {product.quantity}")
    else:
        inventory_event = {
            "order_id": order_id,
            "product_id": product_id,
            "status": "failed",
            "reason": "insufficient stock"
        }
        producer.send('inventory.updated', inventory_event)
        print(f"Insufficient stock for {product_id}")
    
    producer.flush()
    db.close()

def handle_payment_failed(event):
    db = SessionLocal()
    order_id = event['order_id']
    
    if order_id in reservations:
        reservation = reservations[order_id]
        product = db.query(Product).filter(Product.product_id == reservation['product_id']).first()
        
        if product:
            product.quantity += reservation['quantity']
            db.commit()
            print(f"Stock released for order {order_id}: {reservation['product_id']}, new quantity: {product.quantity}")
        
        del reservations[order_id]
    
    db.close()

def start_consumer():
    print("Inventory service started, waiting for orders...")
    for message in consumer:
        event = message.value
        topic = message.topic
        
        if topic == 'order.created':
            print(f"Received order: {event}")
            handle_order_created(event)
        elif topic == 'payment.failed':
            print(f"Payment failed, releasing stock: {event}")
            handle_payment_failed(event)

if __name__ == "__main__":
    start_consumer()
