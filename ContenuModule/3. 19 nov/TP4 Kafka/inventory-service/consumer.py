from kafka import KafkaConsumer
import json
from database import SessionLocal, Product
from kafka_utils import publish_event

reservations = {}

def start_consumer():
    print("Starting inventory consumer...")
    
    consumer = KafkaConsumer(
        'order.created',
        'payment.failed',
        bootstrap_servers='broker:9092',
        group_id='inventory-service',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest'
    )
    
    print("Inventory consumer started, waiting for events...")
    
    for message in consumer:
        event_type = message.topic
        data = message.value
        
        if event_type == 'order.created':
            handle_order_created(data)
        elif event_type == 'payment.failed':
            handle_payment_failed(data)

def handle_order_created(data):
    order_id = data['order_id']
    product_id = data['product_id']
    quantity = data['quantity']
    
    print(f"Received order {order_id} for {quantity}x {product_id}")
    
    db = SessionLocal()
    product = db.query(Product).filter(Product.product_id == product_id).first()
    
    if product and product.quantity >= quantity:
        product.quantity -= quantity
        db.commit()
        reservations[order_id] = {'product_id': product_id, 'quantity': quantity}
        
        print(f"Reserved {quantity} units of {product_id}. New stock: {product.quantity}")
        
        publish_event('inventory.updated', {
            'order_id': order_id,
            'product_id': product_id,
            'quantity': quantity,
            'status': 'reserved'
        })
    else:
        available = product.quantity if product else 0
        print(f"Insufficient stock for {product_id}. Requested: {quantity}, Available: {available}")
        
        publish_event('inventory.updated', {
            'order_id': order_id,
            'product_id': product_id,
            'quantity': quantity,
            'status': 'insufficient_stock'
        })
    
    db.close()

def handle_payment_failed(data):
    order_id = data['order_id']
    
    if order_id in reservations:
        reservation = reservations[order_id]
        product_id = reservation['product_id']
        quantity = reservation['quantity']
        
        print(f"Payment failed for order {order_id}, releasing {quantity}x {product_id}")
        
        db = SessionLocal()
        product = db.query(Product).filter(Product.product_id == product_id).first()
        
        if product:
            product.quantity += quantity
            db.commit()
            print(f"Released {quantity} units of {product_id}. New stock: {product.quantity}")
        
        db.close()
        del reservations[order_id]
