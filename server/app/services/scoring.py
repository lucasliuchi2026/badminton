from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Match, Standing, User


def apply_match(db: Session, player_a: User, player_b: User, score_a: int, score_b: int,
                detail: str, played_at: str, recorded_by: int, activity_id=None) -> Match:
    """录入对局并原子结算积分：胜方 +WIN_POINTS，负方 +LOSE_POINTS。平局拒绝"""
    if player_a.id == player_b.id:
        raise HTTPException(400, "不能与自己对战")
    if score_a == score_b:
        raise HTTPException(400, "比分需分出胜负")
    if score_a < score_b:
        winner, loser, w_score, l_score = player_b, player_a, score_b, score_a
    else:
        winner, loser, w_score, l_score = player_a, player_b, score_a, score_b
    if min(score_a, score_b) < 0 or max(score_a, score_b) > 3 or abs(score_a - score_b) > 2:
        raise HTTPException(400, "三局两制比分不合法（0-3 之间且分差≤2）")

    m = Match(player_a_id=player_a.id, player_b_id=player_b.id, score_a=score_a, score_b=score_b,
              detail=detail, played_at=played_at, recorded_by=recorded_by, activity_id=activity_id)
    db.add(m)
    _add_standing(db, winner.id, settings.WIN_POINTS, win=True)
    _add_standing(db, loser.id, settings.LOSE_POINTS, win=False)
    db.commit()
    return m


def _add_standing(db: Session, user_id: int, points: int, win: bool):
    st = db.get(Standing, user_id)
    if st is None:
        st = Standing(user_id=user_id, points=0, wins=0, losses=0)
        db.add(st)
    st.points += points
    if win:
        st.wins += 1
    else:
        st.losses += 1
