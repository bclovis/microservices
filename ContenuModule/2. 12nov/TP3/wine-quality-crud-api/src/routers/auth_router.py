from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.auth_service import AuthService
from dependencies import get_current_user

router = APIRouter()

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    token = AuthService.authenticate_user(user.username, user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserLogin)
async def read_users_me(current_user: UserLogin = Depends(get_current_user)):
    return current_user