# 打球吗 · 羽毛球群活动管理

微信小程序（测试号）+ FastAPI 后端。功能：活动发布/男女分名额报名/代报名、积分预付局与免费局、历史活动、积分赛自动结算排行、点卡内部记账（无真实资金）、活动素材上传、回顾文案接口（当前模板占位，可换大模型实现）。

> 合规说明：本项目"点卡/积分"仅为群内 AA 记账凭证，不接入任何支付、不可充值提现。

## 目录结构

```
server/            FastAPI 后端（分层：routers 路由 / services 业务 / models 数据 / security 权限）
  app/
    main.py        应用装配、建表、群配置种子
    config.py      环境变量
    db.py          SQLAlchemy engine/session
    models.py      7 张业务表 + 群配置表
    schemas.py     入参校验（pydantic）
    security.py    JWT 签发/校验、require_owner 权限依赖
    wechat.py      code2session（未配 AppID 自动 dev 模式）
    routers/       auth / activities / league / cards / group / misc
    services/      card（点卡原子变更）/ registration（报名+扣分）/ scoring（对局结算）
  schema.sql       建表 SQL（应用会自动建表，此文件供查阅/手动初始化）
  tests/           pytest 单元测试与全流程测试
  Dockerfile fly.toml   免费部署（见 docs/DEPLOY.md）
miniprogram/       微信原生小程序（7 页面，深蓝+荧光绿运动风）
docs/              API.md 接口文档 / DEPLOY.md 部署教程
prototype/         UI 交互原型（浏览器直接打开 index.html）
```

## 快速启动

### 1. 后端
```bash
cd server
python -m venv .venv
.venv\Scripts\activate            # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://127.0.0.1:8000/docs 可看 Swagger
```
- 不配微信也能跑：未设置 WECHAT_APPID 时后端为 dev 登录模式
- 群主规则：**第一个登录的用户自动成为群主**
- 跑测试：`pytest tests -q`

### 2. 小程序
1. 微信开发者工具 → 导入项目 → 选择 `miniprogram/` 目录 → AppID 填你的测试号 AppID（或游客模式）
2. 详情 → 本地设置 → 勾选 **不校验合法域名**
3. `miniprogram/config.js` 中 `BASE_URL` 默认 `http://127.0.0.1:8000`，与本地后端直接联调
4. 编译后即可走通：登录 → 群主发布活动（积分局设男女不同分值）→ 成员报名扣分 → 录分结算 → 调整点卡 → 上传素材 → 生成回顾

### 3. 部署上线
见 `docs/DEPLOY.md`（fly.io 免费档 + 1GB 持久卷 + GitHub Actions 保活）。

## 接口文档
`docs/API.md`，或启动后端后访问 `/docs`（Swagger 自动生成）。

## 关键业务规则（后端强校验，前端仅展示）
- 报名：性别名额原子校验；`paid` 局按所选性别单价 ×人数 从操作人点卡扣分，余额不足直接 400
- 取消：仅本人发起的报名可自行取消；活动未开始时积分原路退还（refund 流水）
- 录分：仅群主；三局两制、需分胜负；胜 +25 / 负 +5 同事务更新 standings
- 点卡：仅群主可 adjust，不允许扣成负数；每次变动必写 card_logs 流水（只增不改）
- 权限：owner/member 一律后端 JWT 校验，403 兜底
