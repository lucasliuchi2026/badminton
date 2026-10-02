import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import User
from ..schemas import LoginIn, ProfileIn
from ..security import create_token, get_current_user
from ..wechat import code_to_openid

router = APIRouter(prefix="/api/auth", tags=["登录"])


def _user_out(u: User):
    return {"id": u.id, "openid": u.openid, "nickname": u.nickname, "avatar": u.avatar,
            "gender": u.gender, "role": u.role, "card_balance": u.card_balance}


@router.post("/login")
async def login(body: LoginIn, db: Session = Depends(get_db)):
    """微信 code 登录；单群模式：第一个注册的用户自动成为群主"""
    if body.appid and settings.WECHAT_APPID and body.appid != settings.WECHAT_APPID:
        # 先拦一层：code 属于小程序侧那个 AppID，跟后端配的不是同一个，交给微信只会回 40029，看不懂
        raise HTTPException(400, f"AppID 不一致：小程序侧 {body.appid}，后端 WECHAT_APPID {settings.WECHAT_APPID}")
    try:
        openid = await code_to_openid(body.code)
    except ValueError as e:
        raise HTTPException(400, f"{e}；后端使用的 AppID={settings.WECHAT_APPID or '（未配置，dev 模式）'}"
                                 f"，小程序侧上报={body.appid or '（未上报）'}")
    user = db.query(User).filter(User.openid == openid).first()
    if user is None:
        is_first = db.query(User).count() == 0
        user = User(openid=openid, role="owner" if is_first else "member",
                    nickname=body.nickname or ("群主" if is_first else "球友"),
                    gender=body.gender if body.gender in ("M", "F") else "M",
                    avatar=body.avatar or "")
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"token": create_token(user), "user": _user_out(user)}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.post("/profile")
def update_profile(body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.nickname:
        user.nickname = body.nickname[:32]
    if body.gender in ("M", "F"):
        user.gender = body.gender
    if body.avatar is not None:
        user.avatar = body.avatar
    db.commit()
    db.refresh(user)
    return _user_out(user)


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """头像上传（chooseAvatar 的临时文件），存 uploads 目录后写入 user.avatar"""
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(413, "头像超过 2MB")
    ext = Path(file.filename or "a").suffix.lower() or ".png"
    name = f"avatar_{user.id}_{uuid.uuid4().hex[:8]}{ext}"
    updir = Path(settings.UPLOAD_DIR)
    updir.mkdir(parents=True, exist_ok=True)
    (updir / name).write_bytes(content)
    user.avatar = f"/uploads/{name}"
    db.commit()
    db.refresh(user)
    return _user_out(user)
