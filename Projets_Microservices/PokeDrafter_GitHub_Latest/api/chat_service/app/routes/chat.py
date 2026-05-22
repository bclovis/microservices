import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.schemas.message import ChatMessage
from app.services import chat_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/api/chat/history")
async def get_chat_history(limit: int = 50):
    return await chat_service.get_history(limit)

# ws://host/ws/chat/{team}?username=Betsaleel
@router.websocket("/ws/chat/{team}")
async def chat_endpoint(
    websocket: WebSocket,
    team: str,
    username: str = Query(...)
):
    logger.info(f"New connection request: team={team}, username={username}")
    
    if team not in ("red", "blue"):
        logger.warning(f"Invalid team: {team}")
        await websocket.close(code=1003)
        return

    try:
        await chat_service.connect(team, websocket)
        logger.info(f"Connected: {username} to {team}")
        
        # User requested to remove "joined" message
        # join_msg = { ... }
        # await chat_service.publish_message(join_msg)

        while True:
            data = await websocket.receive_text()
            logger.info(f"Message from {username} ({team}): {data}")
            msg = {
                "author": username, 
                "content": data, 
                "is_bot": False, 
                "team": team
            }
            # Publish to Kafka so all instances/teams receive it
            await chat_service.publish_message(msg)
            
    except WebSocketDisconnect:
        logger.info(f"Disconnected: {username} from {team}")
        chat_service.disconnect(team, websocket)
        # User requested to remove "left" message
        # leave_msg = { ... }
        # await chat_service.publish_message(leave_msg)
    except Exception as e:
        logger.error(f"Error in chat_endpoint for {username}: {e}")
        chat_service.disconnect(team, websocket)


@router.websocket("/ws/battle/{battle_id}")
async def battle_endpoint(battle_id: str, username: str, websocket: WebSocket):
    room = f"battle_{battle_id}"
    await chat_service.connect(room, websocket)
    
    # User requested to remove "joined" message
    # join_msg = { ... }
    # await chat_service.publish_message(join_msg)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                # If it's JSON, we use it as is
                msg = json.loads(data)
                msg["room"] = room
            except Exception:
                # Otherwise wrap it
                msg = {
                    "type": "chat", 
                    "author": username, 
                    "content": data, 
                    "is_bot": False,
                    "room": room
                }
            await chat_service.publish_message(msg)
    except WebSocketDisconnect:
        chat_service.disconnect(room, websocket)
        # User requested to remove "left" message
        # leave_msg = { ... }
        # await chat_service.publish_message(leave_msg)
