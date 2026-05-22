from fastapi import FastAPI

app = FastAPI(title="Orders Service")

ORDERS = {
    "Alice": [
        {"id": 101, "product": "Laptop", "price": 1200},
        {"id": 102, "product": "Mouse", "price": 25},
    ],
    "Bob": [
        {"id": 201, "product": "Keyboard", "price": 75},
    ],
    "Charlie": [
        {"id": 301, "product": "Monitor", "price": 300},
        {"id": 302, "product": "Webcam", "price": 80},
        {"id": 303, "product": "Headset", "price": 60},
    ],
}

@app.get("/")
def root():
    return {"service": "orders", "status": "running"}

@app.get("/orders/{user}")
def get_orders(user: str):
    """Retourne les commandes d'un utilisateur spécifique"""
    # Si l'utilisateur n'a pas de commandes, retourner une liste vide
    return {"user": user, "orders": ORDERS.get(user, [])}
