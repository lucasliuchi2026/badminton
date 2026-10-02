from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import CardLog, User
from ..schemas import CardAdjustIn
from ..security import get_current_user, require_owner
from ..services.card import change_card

router = APIRouter(prefix="/api/cards", tags=["点卡记账（内部积分，无真实资金）"])


def _log_out(c: CardLog):
    return {"id": c.id, "delta": c.delta, "balance_after": c.balance_after,
            "memo": c.memo, "biz": c.biz, "created_at": c.created_at.strftime("%Y-%m-%d %H:%M")}


@router.get("/mine")
def my_logs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """普通成员仅能看自己的余额与流水"""
    logs = db.query(CardLog).filter(CardLog.user_id == user.id).order_by(CardLog.id.desc()).all()
    return {"card_balance": user.card_balance, "logs": [_log_out(c) for c in logs]}


@router.get("/logs")
def any_logs(user_id: int = Query(...), db: Session = Depends(get_db),
             actor: User = Depends(get_current_user)):
    if actor.role != "owner" and user_id != actor.id:
        raise HTTPException(403, "仅群主可查看他人流水")
    logs = db.query(CardLog).filter(CardLog.user_id == user_id).order_by(CardLog.id.desc()).all()
    return {"user_id": user_id, "logs": [_log_out(c) for c in logs]}


@router.get("/users")
def users_with_balance(db: Session = Depends(get_db), _: User = Depends(require_owner)):
    """群主后台：全员点卡一览（录分选人也复用昵称，走 /api/users）"""
    us = db.query(User).order_by(User.id).all()
    return [{"id": u.id, "nickname": u.nickname, "gender": u.gender,
             "role": u.role, "card_balance": u.card_balance} for u in us]


@router.post("/adjust")
def adjust(body: CardAdjustIn, db: Session = Depends(get_db), owner: User = Depends(require_owner)):
    """点卡充/扣（仅群主）：不允许扣成负数"""
    u = db.get(User, body.user_id)
    if u is None:
        raise HTTPException(404, "成员不存在")
    log = change_card(db, u, body.delta, memo=body.memo, biz="adjust", operator=owner)
    db.commit()
    return {"ok": True, "user_id": u.id, "card_balance": u.card_balance, "log": _log_out(log)}
