from fastapi import FastAPI

app = FastAPI()

users = {
    1: {"user_id": 1, "name": "Betsaleel"},
    2: {"user_id": 2, "name": "Sara"},
    3: {"user_id": 3, "name": "Charlie"}
}

@app.get("/")
def root():
    return {"service": "user-service", "status": "running"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = users.get(user_id)
    if user:
        return user
    return {"error": "User not found"}
