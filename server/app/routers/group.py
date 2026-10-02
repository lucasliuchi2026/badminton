from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import GroupConfig, User
from ..schemas import GroupIn
from ..security import get_current_user, require_owner

router = APIRouter(prefix="/api/group", tags=["群配置"])

DEFAULTS = {
    "club_name": "打球吗 · 羽毛球群",
    "slogan": "无羽伦比，扣杀生活！",
    "intro": "周三 / 周六固定局 · 单打双打混练 · AA记账透明 · 新人欢迎来战。本群点卡仅内部记账，不涉及任何真实资金。",
}


@router.get("")
def get_group(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = {r.key: r.value for r in db.query(GroupConfig).all()}
    return {**DEFAULTS, **rows}


@router.put("")
def update_group(body: GroupIn, db: Session = Depends(get_db), _: User = Depends(require_owner)):
    for k, v in body.model_dump(exclude_none=True).items():
        row = db.get(GroupConfig, k)
        if row is None:
            db.add(GroupConfig(key=k, value=v))
        else:
            row.value = v
    db.commit()
    rows = {r.key: r.value for r in db.query(GroupConfig).all()}
    return {**DEFAULTS, **rows}
