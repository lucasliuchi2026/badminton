from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..security import get_current_user

router = APIRouter(tags=["其他"])


@router.get("/api/users")
def public_users(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """成员基础列表（积分赛选人等），不含点卡余额"""
    return [
        {"id": u.id, "nickname": u.nickname, "gender": u.gender, "role": u.role}
        for u in db.query(User).order_by(User.id).all()
    ]


@router.get("/api/health")
def health():
    return {"ok": True, "app": "badminton-api"}
