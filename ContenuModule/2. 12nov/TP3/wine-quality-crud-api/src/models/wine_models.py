from pydantic import BaseModel
from typing import Optional

class Wine(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    acidity: float
    sweetness: float
    alcohol_content: float
    quality: int

class WineCreate(BaseModel):
    name: str
    type: str
    acidity: float
    sweetness: float
    alcohol_content: float

class WineUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    acidity: Optional[float] = None
    sweetness: Optional[float] = None
    alcohol_content: Optional[float] = None
    quality: Optional[int] = None