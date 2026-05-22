import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.schemas.message import ChatMessage
from app.services import chat_service

router = APIRouter()


# ws://host/ws/chat/{team}?username=Betsaleel
@router.websocket("/ws/chat/{team}")
async def chat_endpoint(team: str, username: str, websocket: WebSocket):
    if team not in ("red", "blue"):
        await websocket.close(code=1003)
        return

    await chat_service.connect(team, websocket)
    join_msg = {"author": "bot", "content": f"{username} a rejoint le chat", "is_bot": True}
    await chat_service.broadcast(team, join_msg)

    try:
        while True:
            data = await websocket.receive_text()
            msg = {"author": username, "content": data, "is_bot": False, "team": team}
            await chat_service.broadcast(team, msg)
    except WebSocketDisconnect:
        chat_service.disconnect(team, websocket)
        leave_msg = {"author": "bot", "content": f"{username} a quitté le chat", "is_bot": True}
        await chat_service.broadcast(team, leave_msg)


@router.websocket("/ws/battle/{battle_id}")
async def battle_endpoint(battle_id: str, username: str, websocket: WebSocket):
    room = f"battle_{battle_id}"
    await chat_service.connect(room, websocket)
    await chat_service.broadcast(room, {"type": "chat", "author": "bot", "content": f"{username} a rejoint la salle", "is_bot": True})

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                msg = {"type": "chat", "author": username, "content": data, "is_bot": False}
            await chat_service.broadcast(room, msg)
    except WebSocketDisconnect:
        chat_service.disconnect(room, websocket)
        await chat_service.broadcast(room, {"type": "chat", "author": "bot", "content": f"{username} a quitté la salle", "is_bot": True})
