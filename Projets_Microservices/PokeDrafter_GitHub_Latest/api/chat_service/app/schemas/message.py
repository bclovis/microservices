from pydantic import BaseModel
from typing import Literal


class ChatMessage(BaseModel):
    team: Literal["red", "blue"]  # canal de diffusion
    author: str
    content: str
    is_bot: bool = False
