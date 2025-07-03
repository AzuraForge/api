# api/src/azuraforge_api/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import settings
from ..services import user_service
from ..database import SessionLocal 

# DİKKAT: Artık parola fonksiyonlarını buradan import ETMİYORUZ.
# Onlar user_service içinde doğrudan password.py'den import edilecek.

# --- OAuth2 Şeması ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/token")

class TokenData(BaseModel):
    username: Optional[str] = None

def create_access_token(data: dict) -> str:
    """Yeni bir JWT oluşturur."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Token'ı doğrular ve mevcut kullanıcıyı döndürür.
    Bu, korunmuş endpoint'lerde bir bağımlılık (dependency) olarak kullanılacak.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Veritabanından kullanıcıyı al
    db = SessionLocal()
    try:
        user = user_service.get_user_by_username(db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return user
    finally:
        db.close()