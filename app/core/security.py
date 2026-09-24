from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    """根据用户 ID 生成 JWT"""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),   # subject，放用户 ID
        "exp": expire,         # 过期时间，jose 会自动校验
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> int | None:
    """从 JWT 中解出用户 ID，失败返回 None"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except (JWTError, ValueError, TypeError):
        return None