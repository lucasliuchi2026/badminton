from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import CardLog, User


def change_card(
    db: Session,
    user: User,
    delta: int,
    memo: str,
    biz: str,
    operator: User,
    allow_negative: bool = False,
) -> CardLog:
    """点卡变动唯一入口：校验 -> 更新余额 -> 记流水，调用方负责 commit"""
    if user.card_balance + delta < 0 and not allow_negative:
        raise HTTPException(400, f"点卡余额不足：当前 {user.card_balance}，本次需 {abs(delta)}，请联系群主记分")
    user.card_balance += delta
    log = CardLog(
        user_id=user.id,
        delta=delta,
        balance_after=user.card_balance,
        memo=memo,
        biz=biz,
        operator_id=operator.id,
    )
    db.add(log)
    return log
