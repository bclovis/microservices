from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import SessionLocal, Order, OutboxEvent
from kafka_producer import publish_event
import json
import threading
import time

app = FastAPI()

class OrderCreate(BaseModel):
    product_id: str
    quantity: int

@app.post("/orders")
def create_order(order: OrderCreate):
    db = SessionLocal()
    
    new_order = Order(
        product_id=order.product_id,
        quantity=order.quantity,
        status="pending"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    order_id = new_order.id
    
    event_payload = {
        "order_id": order_id,
        "product_id": order.product_id,
        "quantity": order.quantity
    }
    
    outbox_event = OutboxEvent(
        event_type="order.created",
        payload=json.dumps(event_payload)
    )
    db.add(outbox_event)
    db.commit()
    
    db.close()
    
    return {"order_id": order_id, "status": "pending"}

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    db.close()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": order.id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": order.status
    }













def process_outbox():
    while True:
        db = SessionLocal()
        events = db.query(OutboxEvent).filter(OutboxEvent.processed == 0).all()
        
        for event in events:
            payload = json.loads(event.payload)
            publish_event(event.event_type, payload)
            event.processed = 1
            db.commit()
        
        db.close()
        time.sleep(5)

threading.Thread(target=process_outbox, daemon=True).start()

@app.get("/")
def root():
    return {"service": "orders"}
