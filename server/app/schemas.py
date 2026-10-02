from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class LoginIn(BaseModel):
    code: str = Field(min_length=1)
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None  # M/F


class ProfileIn(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def _g(cls, v):
        if v is not None and v not in ("M", "F"):
            raise ValueError("gender 必须是 M 或 F")
        return v


class ActivityIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    venue: str = Field(min_length=1, max_length=128)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    time_start: str = Field(pattern=r"^\d{2}:\d{2}$")
    time_end: str = "21:00"
    type: str = "free"  # free/paid
    cost_m: int = 0
    cost_f: int = 0
    cap_m: int = Field(ge=1, le=50)
    cap_f: int = Field(ge=0, le=50)

    @field_validator("type")
    @classmethod
    def _t(cls, v):
        if v not in ("free", "paid"):
            raise ValueError("type 必须是 free 或 paid")
        return v

    @field_validator("cost_m", "cost_f")
    @classmethod
    def _c(cls, v):
        if v < 0:
            raise ValueError("消耗积分不能为负")
        return v


class StatusIn(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def _s(cls, v):
        if v not in ("upcoming", "ongoing", "ended", "cancelled"):
            raise ValueError("非法状态")
        return v


class SignupIn(BaseModel):
    gender: str  # 占用哪个性别名额
    slots: int = Field(ge=1, le=10, default=1)  # 含本人的总名额数
    names: List[str] = []  # 代报成员昵称，长度应等于 slots-1

    @field_validator("gender")
    @classmethod
    def _g(cls, v):
        if v not in ("M", "F"):
            raise ValueError("gender 必须是 M 或 F")
        return v


class MatchIn(BaseModel):
    player_a_id: int
    player_b_id: int
    score_a: int = Field(ge=0, le=3)
    score_b: int = Field(ge=0, le=3)
    detail: str = ""
    played_at: str  # YYYY-MM-DD
    activity_id: Optional[int] = None


class CardAdjustIn(BaseModel):
    user_id: int
    delta: int = Field(ne=0)
    memo: str = Field(min_length=1, max_length=128)


class GroupIn(BaseModel):
    club_name: Optional[str] = None
    slogan: Optional[str] = None
    intro: Optional[str] = None
