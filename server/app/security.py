from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

bearer_scheme = HTTPBearer(auto_error=False)


def create_token(user: User) -> str:
    payload = {
        "uid": user.id,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.TOKEN_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if cred is None:
        raise HTTPException(401, "缺少登录凭证")
    try:
        payload = jwt.decode(cred.credentials, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "登录已过期，请重新进入小程序")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "无效凭证")
    user = db.get(User, payload["uid"])
    if user is None:
        raise HTTPException(401, "用户不存在")
    return user


def require_owner(user: User = Depends(get_current_user)) -> User:
    """敏感操作（建活动/录分/调点卡）仅群主，权限一律后端校验"""
    if user.role != "owner":
        raise HTTPException(403, "仅群主可执行此操作")
    return user
