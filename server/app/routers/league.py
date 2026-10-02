from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Match, Standing, User
from ..schemas import MatchIn
from ..security import get_current_user, require_owner
from ..services.scoring import apply_match

router = APIRouter(prefix="/api/league", tags=["积分赛"])


@router.get("/standings")
def standings(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """实时积分排行榜：按 points 降序"""
    rows = (
        db.query(Standing, User)
        .join(User, User.id == Standing.user_id)
        .order_by(Standing.points.desc(), Standing.wins.desc())
        .all()
    )
    return [
        {"user_id": st.user_id, "nickname": u.nickname, "gender": u.gender,
         "points": st.points, "wins": st.wins, "losses": st.losses}
        for st, u in rows
    ]


@router.get("/matches")
def match_list(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Match).order_by(Match.id.desc()).all()
    names = {u.id: u.nickname for u in db.query(User).all()}
    return [
        {"id": m.id, "date": m.played_at, "a": names.get(m.player_a_id, "?"), "b": names.get(m.player_b_id, "?"),
         "score_a": m.score_a, "score_b": m.score_b, "detail": m.detail}
        for m in rows
    ]


@router.post("/matches")
def record_match(body: MatchIn, db: Session = Depends(get_db), owner: User = Depends(require_owner)):
    """录分（仅群主）：校验比分合法性并自动结算积分"""
    a = db.get(User, body.player_a_id)
    b = db.get(User, body.player_b_id)
    if a is None or b is None:
        raise HTTPException(404, "选手不存在")
    m = apply_match(db, a, b, body.score_a, body.score_b, body.detail, body.played_at,
                    recorded_by=owner.id, activity_id=body.activity_id)
    return {"id": m.id, "ok": True}
