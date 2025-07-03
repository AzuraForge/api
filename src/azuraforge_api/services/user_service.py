# api/src/azuraforge_api/services/user_service.py

from sqlalchemy.orm import Session
from azuraforge_dbmodels import User
from ..schemas import UserCreate
from ..core.security import get_password_hash, verify_password

def get_user_by_username(db: Session, username: str) -> User | None:
    """Verilen kullanıcı adına göre kullanıcıyı bulur."""
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate) -> User:
    """Yeni bir kullanıcı oluşturur."""
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Kullanıcıyı doğrular."""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_default_user_if_not_exists(db: Session):
    """
    Eğer sistemde hiç kullanıcı yoksa, varsayılan bir kullanıcı oluşturur.
    Bu, ilk kurulum için kullanışlıdır.
    """
    print("API: Varsayılan kullanıcı kontrol ediliyor...")
    if db.query(User).count() == 0:
        default_username = "admin"
        default_password = "DefaultPassword123!" # Güçlü bir varsayılan şifre
        
        print(f"API: Hiç kullanıcı bulunamadı. '{default_username}' kullanıcısı oluşturuluyor.")
        print(f"API: UYARI! Lütfen ilk girişten sonra bu şifreyi değiştirin.")
        print(f"API: Kullanıcı Adı: {default_username}")
        print(f"API: Şifre: {default_password}")

        user_in = UserCreate(username=default_username, password=default_password)
        create_user(db, user_in)
        print("API: Varsayılan kullanıcı başarıyla oluşturuldu.")
    else:
        print("API: Mevcut kullanıcılar bulundu, yeni kullanıcı oluşturulmadı.")