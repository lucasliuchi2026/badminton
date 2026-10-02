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

### 2. 注册 Render
- https://render.com → Sign Up → 可用 GitHub 账号直接登录授权。
- 免费档需要验证身份（可绑 Visa/万事达卡或按提示跳过验证仅用免费资源；若无法验证，见文末备选）。

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
- **Disk（可选，$1/月）**：Add Disk → 名称 `badminton-data`、挂载路径 `/data`、1GB。
  - 加盘 → 数据持久，0 元变 1 元/月，**强烈推荐**（几十人群的回忆都在这）。
  - 不加盘 → 纯免费，但**实例重启/重新部署/休眠唤醒后 SQLite 和素材清空**。若如此，把 `DATABASE_URL`、`UPLOAD_DIR` 也删掉（用镜像默认值即可，行为相同）。

### 4. 部署与验证
- 首次 Build 约 3~5 分钟。完成后得到 `https://badminton-api.onrender.com`。
- 浏览器访问 `https://badminton-api.onrender.com/api/health` 应返回 `{"ok":true}`。
- 免费档 15 分钟无请求会休眠，首次访问冷启动约 30~60 秒（保活见第 5 步）。

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
      - run: curl -s https://badminton-api.onrender.com/api/health
```
每 10 分钟 ping 一次基本可保持常驻，冷启动只发生在每次部署后。

## 二、小程序端

### 1. 测试号
- 申请：https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login 获取 AppID/AppSecret
- 小程序后台"开发管理-开发设置-服务器域名"：测试号无需配置合法域名，开发者工具勾选"不校验合法域名"即可

### 2. 导入项目
- 下载微信开发者工具 → 导入项目 → 目录选 `miniprogram/` → AppID 填测试号 AppID（或选"测试号"游客模式）

### 3. 指向后端
- 改 `miniprogram/config.js` 的 `BASE_URL`：本地联调 `http://127.0.0.1:8000`；部署后 `https://badminton-api.onrender.com`
- 本地联调需在开发者工具"详情→本地设置"勾选 **不校验合法域名**

### 4. 正式号域名白名单（将来换正式号时）
- 小程序后台 → 开发设置 → 服务器域名 → request 与 uploadFile 域名均加 `https://badminton-api.onrender.com`

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
