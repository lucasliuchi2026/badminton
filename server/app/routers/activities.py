import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Activity, Media, Registration, User
from ..schemas import ActivityIn, SignupIn, StatusIn
from ..security import get_current_user, require_owner
from ..services import registration as reg_svc

router = APIRouter(prefix="/api/activities", tags=["活动"])

MAX_UPLOAD = 20 * 1024 * 1024  # 单个素材 20MB 上限，适配免费存储


def _activity_out(a: Activity, db: Session, with_regs: bool = False):
    regs = (
        db.query(Registration)
        .filter(Registration.activity_id == a.id, Registration.status == "active")
        .all()
    )
    men = [r for r in regs if r.gender == "M"]
    women = [r for r in regs if r.gender == "F"]
    out = {
        "id": a.id, "name": a.name, "venue": a.venue, "date": a.date,
        "time_start": a.time_start, "time_end": a.time_end,
        "type": a.type, "cost_m": a.cost_m, "cost_f": a.cost_f,
        "cap_m": a.cap_m, "cap_f": a.cap_f, "status": a.status,
        "signed_m": len(men), "signed_f": len(women), "signed_total": len(regs),
    }
    if with_regs:
        def fmt(r: Registration):
            return {"id": r.id, "member_name": r.member_name, "paid": r.paid,
                    "creator_id": r.creator_id, "is_self": r.member_id == r.creator_id}
        out["registrations_m"] = [fmt(r) for r in men]
        out["registrations_f"] = [fmt(r) for r in women]
        out["media"] = [
            {"id": m.id, "kind": m.kind, "url": m.url}
            for m in db.query(Media).filter(Media.activity_id == a.id).order_by(Media.id.desc()).all()
        ]
    return out


@router.get("")
def list_activities(
    scope: str = Query("active", pattern="^(active|history)$"),
    keyword: str = "",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """scope=active 返回有效未结束活动（广场），scope=history 返回已结束/取消（历史页）"""
    q = db.query(Activity)
    if scope == "active":
        q = q.filter(Activity.status.in_(("upcoming", "ongoing")))
    else:
        q = q.filter(Activity.status.in_(("ended", "cancelled")))
    acts = q.order_by(Activity.date.desc(), Activity.id.desc()).all()
    if keyword:
        acts = [a for a in acts if keyword in a.name or keyword in a.venue]
    return [_activity_out(a, db) for a in acts]


@router.get("/{activity_id}")
def get_activity(activity_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    a = db.get(Activity, activity_id)
    if a is None:
        raise HTTPException(404, "活动不存在")
    return _activity_out(a, db, with_regs=True)


@router.post("")
def create_activity(body: ActivityIn, db: Session = Depends(get_db), owner: User = Depends(require_owner)):
    a = Activity(**body.model_dump(), created_by=owner.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return _activity_out(a, db)


@router.put("/{activity_id}")
def update_activity(activity_id: int, body: ActivityIn, db: Session = Depends(get_db),
                    _: User = Depends(require_owner)):
    a = db.get(Activity, activity_id)
    if a is None:
        raise HTTPException(404, "活动不存在")
    for k, v in body.model_dump().items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return _activity_out(a, db)


@router.post("/{activity_id}/status")
def change_status(activity_id: int, body: StatusIn, db: Session = Depends(get_db),
                  _: User = Depends(require_owner)):
    a = db.get(Activity, activity_id)
    if a is None:
        raise HTTPException(404, "活动不存在")
    a.status = body.status
    db.commit()
    return _activity_out(a, db)


@router.get("/mine/registrations")
def my_registrations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """我报名/代报参与过的活动（个人中心用）"""
    regs = (
        db.query(Registration)
        .filter(Registration.status == "active",
                (Registration.member_id == user.id) | (Registration.member_name == user.nickname))
        .all()
    )
    out, seen = [], set()
    for r in regs:
        if r.activity_id in seen:
            continue
        seen.add(r.activity_id)
        a = db.get(Activity, r.activity_id)
        if a:
            out.append({"activity_id": a.id, "name": a.name, "date": a.date,
                        "time_start": a.time_start, "venue": a.venue, "status": a.status, "paid": r.paid})
    return sorted(out, key=lambda x: x["date"], reverse=True)


@router.post("/{activity_id}/signup")
def signup(activity_id: int, body: SignupIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = db.get(Activity, activity_id)
    if a is None:
        raise HTTPException(404, "活动不存在")
    regs = reg_svc.signup(db, a, user, body.gender, body.slots, body.names)
    return {"created": len(regs), "activity": _activity_out(a, db)}


@router.post("/registrations/{reg_id}/cancel")
def cancel(reg_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = db.get(Registration, reg_id)
    if r is None:
        raise HTTPException(404, "报名记录不存在")
    reg_svc.cancel(db, r, user, db.get(Activity, r.activity_id))
    return {"ok": True}


@router.get("/{activity_id}/review")
def review(activity_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """活动回顾文案：当前为模板生成占位，后续可替换为大模型实现（接口不变）"""
    a = db.get(Activity, activity_id)
    if a is None:
        raise HTTPException(404, "活动不存在")
    stats = _activity_out(a, db, with_regs=True)
    names = [x["member_name"] for x in stats["registrations_m"] + stats["registrations_f"]]
    text = (
        f"【活动回顾】{a.date} {a.time_start}-{a.time_end}，「{a.name}」在{a.venue}圆满结束。\n"
        f"本场共 {stats['signed_total']} 人出战（♂{stats['signed_m']} / ♀{stats['signed_f']}）："
        f"{'、'.join(names) if names else '暂无报名记录'}。\n"
        f"现场照片 {len(stats['media'])} 个素材已归档。无羽伦比，扣杀生活——下次球场见！"
    )
    return {"activity_id": a.id, "text": text, "engine": "template"}


@router.post("/{activity_id}/media")
async def upload_media(activity_id: int, file: UploadFile = File(...), kind: str = Form("photo"),
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """素材上传：multipart 存本地磁盘（部署挂持久卷），url 走 /uploads 静态访问"""
    if kind not in ("photo", "video"):
        raise HTTPException(400, "kind 必须是 photo 或 video")
    if db.get(Activity, activity_id) is None:
        raise HTTPException(404, "活动不存在")
    content = await file.read()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(413, "文件超过 20MB 限制，请压缩后上传")
    ext = Path(file.filename or "f").suffix.lower() or (".jpg" if kind == "photo" else ".mp4")
    name = f"{activity_id}_{uuid.uuid4().hex}{ext}"
    updir = Path(settings.UPLOAD_DIR)
    updir.mkdir(parents=True, exist_ok=True)
    (updir / name).write_bytes(content)
    m = Media(activity_id=activity_id, uploader_id=user.id, kind=kind, url=f"/uploads/{name}", size=len(content))
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "kind": m.kind, "url": m.url, "size": m.size}
