import os
import sys
import tempfile

# 必须在导入 app 之前设置环境变量：测试用独立临时库
_tmp = tempfile.mkdtemp(prefix="badminton_test_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_tmp, "test.db").replace("\\", "/")
os.environ["UPLOAD_DIR"] = os.path.join(_tmp, "uploads")
os.environ["JWT_SECRET"] = "test-secret-0123456789abcdef0123456789abcdef"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402
from app.db import Base, engine  # noqa: E402
import app.models  # noqa: E402,F401  确保建表元数据加载
from app.main import app  # noqa: E402

# TestClient 非 with 用法不跑 lifespan，这里显式建表
Base.metadata.create_all(engine)

client = TestClient(app)


def login(code: str, nickname: str = None, gender: str = "M") -> dict:
    """dev 模式登录（未配 AppID 时 openid = dev-<code>），返回 {token,user}"""
    body = {"code": code}
    if nickname:
        body.update(nickname=nickname, gender=gender)
    resp = client.post("/api/auth/login", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


def auth(token: str) -> dict:
    return {"Authorization": "Bearer " + token}
