from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

from src.config import Config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_access_token(email: str, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "email": email}
    encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ENCODE_ALGORITHM)
    return encoded_jwt


async def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


async def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
