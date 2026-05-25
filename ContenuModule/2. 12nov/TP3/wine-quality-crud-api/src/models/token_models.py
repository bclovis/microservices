from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    expires: datetime

class TokenData(BaseModel):
    username: str | None = None
    scopes: list[str] = []