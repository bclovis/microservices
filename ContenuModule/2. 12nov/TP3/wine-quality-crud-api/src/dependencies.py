from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from .config import settings
from .models.user_models import User
from .services.auth_service import get_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = get_current_user(username)
    except JWTError:
        raise credentials_exception
    if token_data is None:
        raise credentials_exception
    return token_data