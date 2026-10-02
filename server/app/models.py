from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from .db import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    openid = Column(String(64), unique=True, nullable=False)
    nickname = Column(String(32), nullable=False, default="球友")
    avatar = Column(String(255), nullable=False, default="")
    gender = Column(String(1), nullable=False, default="M")  # M/F
    role = Column(String(10), nullable=False, default="member")  # owner/member
    card_balance = Column(Integer, nullable=False, default=0)  # 点卡余额（内部记账）
    created_at = Column(DateTime, default=_utcnow)


class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    venue = Column(String(128), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    time_start = Column(String(5), nullable=False)
    time_end = Column(String(5), nullable=False, default="21:00")
    type = Column(String(10), nullable=False, default="free")  # free/paid
    cost_m = Column(Integer, nullable=False, default=0)  # 男生每人消耗积分
    cost_f = Column(Integer, nullable=False, default=0)  # 女生每人消耗积分
    cap_m = Column(Integer, nullable=False, default=0)
    cap_f = Column(Integer, nullable=False, default=0)
    status = Column(String(10), nullable=False, default="upcoming")  # upcoming/ongoing/ended/cancelled
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 操作人（代报时从其点卡扣分）
    member_id = Column(Integer, ForeignKey("users.id"))  # 已知成员可关联，代报新人可空
    member_name = Column(String(32), nullable=False)
    gender = Column(String(1), nullable=False)
    paid = Column(Integer, nullable=False, default=0)
    status = Column(String(10), nullable=False, default="active")  # active/cancelled
    created_at = Column(DateTime, default=_utcnow)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"))
    player_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    player_b_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score_a = Column(Integer, nullable=False)
    score_b = Column(Integer, nullable=False)
    detail = Column(String(128), nullable=False, default="")
    played_at = Column(String(10), nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class Standing(Base):
    __tablename__ = "standings"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    points = Column(Integer, nullable=False, default=0)
    wins = Column(Integer, nullable=False, default=0)
    losses = Column(Integer, nullable=False, default=0)


class CardLog(Base):
    __tablename__ = "card_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delta = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    memo = Column(String(128), nullable=False)
    biz = Column(String(16), nullable=False)  # signup/refund/adjust
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)


class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kind = Column(String(8), nullable=False)  # photo/video
    url = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow)


class GroupConfig(Base):
    __tablename__ = "group_config"
    key = Column(String(32), primary_key=True)
    value = Column(Text, nullable=False)
