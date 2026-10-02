from typing import List

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Activity, Registration, User
from .card import change_card


def gender_count(db: Session, activity_id: int, gender: str) -> int:
    return (
        db.query(func.count(Registration.id))
        .filter(Registration.activity_id == activity_id,
                Registration.status == "active",
                Registration.gender == gender)
        .scalar()
        or 0
    )


def signup(
    db: Session,
    activity: Activity,
    creator: User,
    gender: str,
    slots: int,
    names: List[str],
) -> List[Registration]:
    """报名/代报名：性别名额校验 + 积分局原子扣分（积分从操作人点卡扣）。规则以后端为准"""
    if activity.status not in ("upcoming", "ongoing"):
        raise HTTPException(400, "该活动已结束或已取消，无法报名")
    cap = activity.cap_m if gender == "M" else activity.cap_f
    used = gender_count(db, activity.id, gender)
    if slots > cap - used:
        raise HTTPException(400, f"{'男' if gender == 'M' else '女'}生名额不足：剩余 {max(cap - used, 0)} 个")
    if len(names) + 1 != slots:
        raise HTTPException(400, "代报昵称数量与名额数不一致（names 数应等于 slots-1）")

    unit = (activity.cost_m if gender == "M" else activity.cost_f) if activity.type == "paid" else 0
    pay_total = unit * slots

    regs: List[Registration] = [
        Registration(activity_id=activity.id, creator_id=creator.id, member_id=creator.id,
                     member_name=creator.nickname, gender=gender, paid=unit, status="active")
    ]
    for i in range(slots - 1):
        name = names[i].strip() if i < len(names) and names[i].strip() else f"代报{i + 1}"
        target = db.query(User).filter(User.nickname == name).first()
        regs.append(
            Registration(activity_id=activity.id, creator_id=creator.id,
                         member_id=target.id if target else None,
                         member_name=name, gender=gender, paid=unit, status="active")
        )

    if pay_total > 0:
        # 余额不足会在这里 400 中断，前面的 Registration 尚未 commit，不会产生脏数据
        change_card(
            db, creator, -pay_total,
            memo=f"「{activity.name}」报名预付积分 ×{slots}人（{'♂' if gender == 'M' else '♀'}{unit}分/人）",
            biz="signup", operator=creator,
        )
    db.add_all(regs)
    db.commit()
    for r in regs:
        db.refresh(r)
    return regs


def cancel(db: Session, reg: Registration, actor: User, activity: Activity):
    """取消报名：仅本人发起的报名可自行取消（群主可取消任意）；活动未开始时按名额单价退还给付款人"""
    if actor.role != "owner" and reg.creator_id != actor.id:
        raise HTTPException(403, "只能取消自己发起的报名")
    if reg.status != "active":
        raise HTTPException(400, "该报名已取消")
    reg.status = "cancelled"
    payer = db.get(User, reg.creator_id)
    if reg.paid > 0 and activity.status == "upcoming":
        change_card(db, payer, +reg.paid,
                    memo=f"「{activity.name}」取消报名退还积分", biz="refund", operator=actor)
    db.commit()
