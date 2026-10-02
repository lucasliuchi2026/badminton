from app.db import SessionLocal
from app.models import Standing, User
from app.services.scoring import apply_match
from app.services import card as card_svc
from fastapi import HTTPException
import pytest


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


def _mkuser(db, name, bal=100):
    u = User(openid="unit-" + name, nickname=name, card_balance=bal)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def test_winner_gets_25_loser_gets_5(db):
    a, b = _mkuser(db, "unitA"), _mkuser(db, "unitB")
    apply_match(db, a, b, 2, 1, "21-15,18-21,21-13", "2026-10-01", recorded_by=a.id)
    sa = db.query(Standing).filter_by(user_id=a.id).first()
    sb = db.query(Standing).filter_by(user_id=b.id).first()
    assert (sa.points, sa.wins, sa.losses) == (25, 1, 0)
    assert (sb.points, sb.wins, sb.losses) == (5, 0, 1)


def test_draw_rejected(db):
    a, b = _mkuser(db, "unitC"), _mkuser(db, "unitD")
    with pytest.raises(HTTPException):
        apply_match(db, a, b, 1, 1, "", "2026-10-01", recorded_by=a.id)


def test_self_match_rejected(db):
    a = _mkuser(db, "unitE")
    with pytest.raises(HTTPException):
        apply_match(db, a, a, 2, 0, "", "2026-10-01", recorded_by=a.id)


def test_card_cannot_go_negative(db):
    u = _mkuser(db, "unitF", bal=10)
    with pytest.raises(HTTPException):
        card_svc.change_card(db, u, -30, "扣减", "adjust", u)
    card_svc.change_card(db, u, +50, "记分", "adjust", u)
    db.commit()
    assert u.card_balance == 60
