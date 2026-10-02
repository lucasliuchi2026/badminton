from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import Base, engine, get_db
from .models import GroupConfig
from .routers import activities, auth, cards, group, league, misc

app = FastAPI(title="打球吗 API", version="1.0.0", description="羽毛球群活动管理 · 单群内部记账")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 小程序请求不受 CORS 限制，放开便于 H5 调试
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth.router, activities.router, league.router, cards.router, group.router, misc.router):
    app.include_router(r)


@app.on_event("startup")
def startup():
    """建表 + 群配置默认值（单群模式，无多租户）"""
    if settings.DATABASE_URL.startswith("sqlite"):
        # 容器内没有持久盘时 /data 或 ./data 可能不存在，建库前先建目录
        Path(settings.DATABASE_URL.split("///")[-1]).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    db = next(get_db())
    for k, v in group.DEFAULTS.items():
        if db.get(GroupConfig, k) is None:
            db.add(GroupConfig(key=k, value=v))
    db.commit()
    db.close()
