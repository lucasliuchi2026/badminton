# 部署说明（全免费方案）

架构：微信小程序（测试号） → FastAPI 后端（Render 免费档） → SQLite（Render 磁盘或容器内） → 素材存 /data/uploads。

> 网络提示：当前国内网络直连 **fly.io 注册/登录域名不可达**（api.machines.dev 可达但 OAuth 入口被挡），Render / Neon / Railway 可直连。因此默认走 Render，fly.io 方案保留在文末。

## 一、后端部署到 Render

### 1. 准备 GitHub 仓库
Render 从 Git 仓库拉代码构建。在项目根目录：
```bash
cd D:/code/badminton
git init -b main
git add .
git commit -m "打球吗 v1：FastAPI 后端 + 微信小程序"
```
然后在 GitHub 新建仓库（建议 Private），`git remote add origin ... && git push -u origin main`。

### 2. 注册 Render 并绑卡（必须）
- https://render.com → Sign Up → 可用 GitHub 账号直接登录授权。
- **注意：创建 free 实例也要求先在 https://dashboard.render.com/billing 绑一张 Visa/万事达卡**（free 档按 $0 计费，仅用于身份验证）。未绑卡时 API 建服务会返回 `402 Payment information is required`。
- 若无法绑卡：见文末备选方案。

### 3. 创建 Web Service
- Dashboard → **New + → Web Service** → 选中刚才的 GitHub 仓库 → 若仓库根目录带本项目的 `render.yaml`，Blueprint 会自动导入以下配置；也可手动填：

| 项 | 值 |
|---|---|
| Root Directory | `server` |
| Runtime | Docker（自动识别 Dockerfile） |
| Environment | Docker |
| Instance Type | **Free** |
| Region | Singapore（就近） |
| Health Check Path | `/api/health` |

- 环境变量（Environment Variables）：
  - `JWT_SECRET`：一串随机长字符串（32 位以上）
  - `DATABASE_URL`：`sqlite:////data/badminton.db`
  - `UPLOAD_DIR`：`/data/uploads`
  - `WECHAT_APPID` / `WECHAT_SECRET`：测试号的 AppID 与 AppSecret（见下方 4.2）
- **Disk（可选，$1/月）**：Add Disk → 名称 `badminton-data`、挂载路径 `/data`、1GB。
  - 加盘 → 数据持久，0 元变 1 元/月，**强烈推荐**（几十人群的回忆都在这）。
  - 不加盘 → 纯免费，但**实例重启/重新部署/休眠唤醒后 SQLite 和素材清空**。若如此，把 `DATABASE_URL`、`UPLOAD_DIR` 也删掉（用镜像默认值即可，行为相同）。
  - 实测确认：本次不带盘重启后，用户 id 从头自增、活动记录全部消失，行为与文档一致。当前线上为"无盘"状态，正式给群友用之前建议加盘。

### 4. 部署与验证
- 首次 Build 约 3~5 分钟。完成后得到 `https://badminton-api-5k6c.onrender.com`。
- 浏览器访问 `https://badminton-api-5k6c.onrender.com/api/health` 应返回 `{"ok":true,"app":"badminton-api"}`。
- 免费档 15 分钟无请求会休眠，首次访问冷启动约 30~60 秒（保活见第 5 步）。
- ✅ 本仓库已按上述配置部署并通过线上冒烟：登录 → 建收费局 → 点卡调整 → 报名扣卡 → 取消退费 → 记分 → 战报，权限（403）、名额/人数校验、余额不足（400）均符合预期（31 项断言全过）。
  注：那次冒烟跑在开发登录模式下（凭据未配，可用任意假 code 造账号）。配好 `WECHAT_APPID` 后假 code 会返回 40029，线上不便再跑全自动冒烟 —— 回归请走本地 `uvicorn`（不设微信变量）+ `pytest`，真机登录验证交给开发者工具/手机端。

### 4.1 代码更新后如何重新部署
**重要**：这个服务是在 Render 网页上手动填仓库 URL 创建的（不是授权 GitHub App 的仓库连接），`autoDeploy` 不会自动触发。每次 push 新代码后需手动部署，二选一：
- Dashboard → 服务 → **Manual Deploy → Deploy latest commit**；
- 或 API（把 `<key>` 换成 Account → API Keys 里的密钥，`srv-...` 换成自己的服务 id）：
```bash
curl -X POST "https://api.render.com/v1/services/srv-davh4vmk1f9s73aa80ag/deploys" \
  -H "Authorization: Bearer <key>" -H "Content-Type: application/json" \
  -d '{"revision":"main"}'
```
构建约 1~2 分钟，成功后新版本自动切流量。想恢复自动部署，可在 Dashboard 该服务的 Settings → Deploy → 重新连接 GitHub 仓库授权。

### 4.2 微信登录凭据（已配置并实测通过）
- 作用：未设置 `WECHAT_APPID` / `WECHAT_SECRET` 时后端走**开发登录模式**（openid = `dev-<code>`），每次 `wx.login` 拿到新 code 都会注册一个新账号，身份不持久、点卡记录存不住。真机使用前必须配上。
- 在哪查：**测试号** https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login 微信扫码登录，页面第一屏即「开发者ID(AppID)」和「开发者密码(AppSecret，点生成/重置后显示明文）」；**正式号** mp.weixin.qq.com →「开发」→「开发管理」→「开发设置」。
- 现状（2026-10-02）：测试号 AppID/AppSecret 已写入本服务环境变量并重新部署。用假 code 探 `POST /api/auth/login` 返回 `400 微信登录失败: invalid code (errcode=40029)` —— 这恰好证明三件事：凭据已生效（不再是 dev 模式）、AppID/AppSecret 被微信接受、**Render 新加坡出口 IP 不在微信 40164 白名单拦截名单里**。换真 `wx.login` 的 code 即可正常登录。
- ⚠️ 用 API 改变量时的坑：`PUT /v1/services/{id}/env-vars` 是**整体替换**语义，只提交新键会把 `JWT_SECRET` 等旧键删掉（`POST .../env-vars` 在此接口返回 405）。正确做法是 GET 现有全部键、合并后整份 PUT；单个键改动可用 `PATCH /v1/services/{id}/env-vars/{key}`。改完必须再触发一次部署（§4.1）才生效。

### 5. 保活（GitHub Actions，免费）
新建 `.github/workflows/keepalive.yml`：
```yaml
name: keepalive
on:
  schedule: [{ cron: "*/10 * * * *" }]
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl -s https://badminton-api-5k6c.onrender.com/api/health
```
每 10 分钟 ping 一次基本可保持常驻，冷启动只发生在每次部署后。
本仓库已带 `.github/workflows/keepalive.yml`（GitCode 上也有该文件）。注意：**push 到 GitHub 的 `.github/workflows/**` 需要 PAT 带 `workflow` 权限**，否则 GitHub 返回 404 拒绝写入。若你的 token 没这个 scope，直接在 GitHub 网页 New file → 路径填 `.github/workflows/keepalive.yml` → 粘贴上面内容 → Commit 即可。

## 二、小程序端

### 1. 测试号
- 申请：https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login 获取 AppID/AppSecret
- 小程序后台"开发管理-开发设置-服务器域名"：测试号无需配置合法域名，开发者工具勾选"不校验合法域名"即可

### 2. 导入项目
- 下载微信开发者工具 → 导入项目 → 目录选 `miniprogram/` → AppID 填测试号 AppID（或选"测试号"游客模式）

### 3. 指向后端
- 改 `miniprogram/config.js` 的 `BASE_URL`：本地联调 `http://127.0.0.1:8000`；部署后 `https://badminton-api-5k6c.onrender.com`
- 本地联调需在开发者工具"详情→本地设置"勾选 **不校验合法域名**

### 4. 正式号域名白名单（将来换正式号时）
- 小程序后台 → 开发设置 → 服务器域名 → request 与 uploadFile 域名均加 `https://badminton-api-5k6c.onrender.com`

### 5. 真机预览给群友
- 开发者工具点"预览"生成二维码；群友首次打开后，需在小程序右上角"…"→ 开发调试（vConsole）→ 开启调试，才能请求非白名单域名（测试号特性）
- 或在开发者工具"项目设置"里把体验者加进测试号后台"测试者"列表

### 6. 群主与成员
- **第一个登录小程序的用户自动成为群主**（后端规则），请用你自己的微信号先登录
- 其他成员登录后默认 member，群主在"管理后台"给他们记分即可

## 三、备选方案

| 平台 | 说明 |
|---|---|
| fly.io（原文案） | 1GB 卷免费、休眠可恢复；**国内直连注册/登录被挡**，需代理。命令见下方附录 |
| Railway | https://railway.app 可直连，一次性 $5 试用额度，无永久免费档，适合临时演示 |
| Render + Neon + R2 | 纯免费且持久：DATABASE_URL 换 Neon 免费 Postgres（需给 requirements 加 psycopg2-binary、URL 改 postgresql+psycopg://），uploads 换 Cloudflare R2（需改代码走 S3 API，工程量最大） |
| 自家电脑 + cloudflared | `cloudflared tunnel --url http://127.0.0.1:8000` 得临时 https；电脑关机即断，trycloudflare 国内直连不稳定 |

## 附录：fly.io 部署（需可访问 fly.io 的网络）

```bash
cd server
fly auth login                      # 注册需绑卡；国内需代理完成 OAuth
fly apps create badminton-api       # 与 fly.toml 的 app 名保持一致
fly volumes create badminton_data --region nrt --size 1
fly deploy
fly secrets set JWT_SECRET=... WECHAT_APPID=... WECHAT_SECRET=...
```
flyctl 免管理员安装：从 GitHub releases 下载 `flyctl_<ver>_windows_x86_64.zip` 解压到 `%LOCALAPPDATA%\flyctl` 并加入 PATH。

## 四、数据备份

Render 加了磁盘时，可在 Render 磁盘页手动快照；或 CLI（Dashboard → Account → API Keys 生成密钥）：
```bash
render disks create-snapshot <diskId> --api-key $RENDER_API_KEY
```
fly.io 路线：
```bash
fly ssh console -C /data -c "tar czf - ." > backup.tgz
```
建议每月一次；几十人规模全量 < 50MB。
