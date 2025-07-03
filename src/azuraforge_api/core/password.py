# api/src/azuraforge_api/core/password.py

from passlib.context import CryptContext

# Bu modül sadece parola işlemleriyle ilgilenir ve başka hiçbir
# proje modülüne bağımlı değildir.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Verilen parolayı hash'ler."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Parolayı hash ile karşılaştırır."""
    return pwd_context.verify(plain_password, hashed_password)