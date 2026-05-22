from collections import defaultdict
from typing import Dict, List
from fastapi import WebSocket

# connexions groupées par team : "red" ou "blue"
_connections: Dict[str, List[WebSocket]] = defaultdict(list)


async def connect(team: str, ws: WebSocket):
    await ws.accept()
    _connections[team].append(ws)


def disconnect(team: str, ws: WebSocket):
    try:
        _connections[team].remove(ws)
    except ValueError:
        pass


async def broadcast(team: str, message: dict):
    if team not in _connections:
        return
    dead = []
    for ws in _connections[team]:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        disconnect(team, ws)


async def broadcast_all(message: dict):
    for team in ["red", "blue"]:
        await broadcast(team, message)
