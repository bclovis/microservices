from fastapi import FastAPI

app = FastAPI(title="Users Service")

# Données en dur - pas de BDD
USERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
]

@app.get("/")
def root():
    return {"service": "users", "status": "running"}

@app.get("/users")
def get_users():
    """Retourne la liste de tous les utilisateurs"""
    return {"users": USERS}
