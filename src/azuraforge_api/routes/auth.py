# api/src/azuraforge_api/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core import security
from ..services import user_service
from ..schemas import Token, UserCreate
from ..database import SessionLocal, engine
from azuraforge_dbmodels import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Veritabanı session'ını bir bağımlılık olarak almak için
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Kullanıcı adı ve parola ile giriş yaparak JWT alır."""
    user = user_service.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=dict)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Yeni bir kullanıcı kaydeder."""
    db_user = user_service.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    created_user = user_service.create_user(db=db, user=user)
    return {"message": "User registered successfully", "username": created_user.username}

@router.get("/users/me", response_model=dict)
def read_users_me(current_user: User = Depends(security.get_current_user)):
    """Geçerli token'a sahip kullanıcının bilgilerini döndürür."""
    return {"username": current_user.username, "created_at": current_user.created_at}