from pydantic import BaseModel
from typing import Optional
import bcrypt

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None

class WineData(BaseModel):
    fixed_acidity: float
    volatile_acidity: float
    citric_acid: float
    residual_sugar: float
    chlorides: float
    free_sulfur_dioxide: float
    total_sulfur_dioxide: float
    density: float
    pH: float
    sulphates: float
    alcohol: float
    quality: int

class WineResponse(WineData):
    id: int

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

fake_users_db = {
    "betsaleel": {
        "username": "betsaleel",
        "full_name": "Betsaleel",
        "email": "betsaleel@cy-tech.fr",
        "hashed_password": "$2b$12$/5.5t4zsQagdXHi8egABJOgpONGxhAezkhpnAT4pCcRzERQWplVmi",
        "disabled": False,
    },
    "clovis": {
        "username": "clovis",
        "full_name": "Clovis",
        "email": "clovis@cy-tech.fr",
        "hashed_password": "$2b$12$OJ26VJ12Oat4PcWeW2g4CeJJHMPsQkAk4Zf/pd8L11.5rySRC0Ley",
        "disabled": False,
    },
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@cy-tech.fr",
        "hashed_password": "$2b$12$fyU5nA8Sf6kIqF8fJ1LSqOgHr8K/BZoFxLz4jYDYQvsuWLmAXn4oe",
        "disabled": False,
    }
}

def get_user(username: str) -> Optional[UserInDB]:
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
