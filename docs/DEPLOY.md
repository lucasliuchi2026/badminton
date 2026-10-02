# 部署说明（全免费方案）

架构：微信小程序（个人主体，免费） → FastAPI 后端（Render 免费档） → SQLite（Render 磁盘或容器内） → 素材存 /data/uploads。

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
  - `WECHAT_APPID` / `WECHAT_SECRET`：**小程序**账号的 AppID 与 AppSecret（见 §4.2 与 §二.1，别用公众号测试号的）
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
- AppID/AppSecret 从哪来：**必须是「小程序」账号的**。用 mp.weixin.qq.com 首页「立即注册」→ 类型选 **小程序** → 主体选 **个人**（免费、不需微信认证，需身份证+本人手机号），注册完成后在「开发管理 → 开发设置」里拿 AppID 和 AppSecret（生成密钥要管理员扫码）。
  ⚠️ 坑（2026-10-02 踩过）：`mp.weixin.qq.com/debug/cgi-bin/sandbox` 是**公众号接口测试号**，它第一屏的 AppID/AppSecret 也能通过 `jscode2session` 的凭据校验（不报 40013/40125），但换不出小程序 `wx.login` 的 code，只回一个含糊的 `40029 invalid code`。文档这里曾经推荐过那个页面，是错的。
- 现状（2026-10-02）：服务上已配了一对 AppID/AppSecret 并重新部署（`GET /api/health` 会回报 `wechat_login: "prod"` 和当前 appid，不用登后台）。实测两件事：① 用假 code 打登录回 `40029`，而不是 `40164`，说明 **Render 新加坡出口 IP 不在微信 IP 白名单拦截范围**；② 用开发者工具现取的新 code 直接打 `jscode2session` 仍回 `40029` —— 说明这对凭据是**公众号测试号**的，小程序登录要换成真正的「小程序」AppID/AppSecret 才能通。
  另外：`40029` 只能说明"code 不属于这个 AppID"，**不能**证明 AppID 是小程序账号（微信先验凭据格式与配对，再验 code）。
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

### 1. 注册一个小程序账号（拿 AppID / AppSecret）
- 入口：https://mp.weixin.qq.com 首页 →「立即注册」→ 类型选 **小程序** → 主体类型选 **个人**（免费、不需 300 元微信认证；需要身份证、本人手机号、人脸核验；注册邮箱须未绑定过公众号/小程序）
- 注册好之后：登录后台 →「开发管理」→「开发设置」→ 顶部就是 **AppID(小程序ID)**，**AppSecret(小程序密钥)** 点「生成」并让管理员微信扫码后才显示明文
- ⚠️ 不要用 `mp.weixin.qq.com/debug/cgi-bin/sandbox` 那个页面 —— 它是**公众号**接口测试号，它的 AppID 换不出小程序 `wx.login` 的 code（只报含糊的 `40029`），本项目踩过这个坑
- 判定一个 AppID 到底是公众号还是小程序（两条只读调用，58 秒出结论）：
```bash
T=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=<AppID>&secret=<AppSecret>" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
curl -s -X POST "https://api.weixin.qq.com/wxa/get_qrcode?access_token=$T" -H 'Content-Type: application/json' -d '{"path":"pages/index/index"}'   # 小程序专有
curl -s "https://api.weixin.qq.com/cgi-bin/user/get?access_token=$T&next_openid="                                                                # 公众号专有
```
  小程序专有接口回 `48001 api unauthorized` 而公众号接口正常返回 → 这是**公众号**（本项目当时就是这个结果）
- 拿到 AppID 后**两处要一致**：后端环境变量 `WECHAT_APPID`/`WECHAT_SECRET` = `miniprogram/project.config.json` 的 `appid`（改完 project.config.json 要关项目重开）
- 域名白名单：正式小程序会校验请求域名，须在「开发设置 → 服务器域名」把 `https://badminton-api-5k6c.onrender.com` 同时加进 **request** 和 **uploadFile** 两个列表；开发者工具里可以先勾「不校验合法域名」绕过，真机则必须配好
- 自检 appid/secret 是否配对（返回 `40029` 表示凭据被认、只是 code 是假的；`40125` 表示 secret 与该 appid 不配对；`40013` 表示 appid 不存在）：
```bash
curl "https://api.weixin.qq.com/sns/jscode2session?appid=<AppID>&secret=<AppSecret>&js_code=probe&grant_type=authorization_code"
```

### 2. 导入项目
- 下载微信开发者工具 → 右上角用**该小程序管理员的微信号**登录 → 导入项目 → 目录选 `miniprogram/` → AppID 填刚注册的小程序 AppID
- 「游客模式 / 测试号」不能用于换 openid（换出来的 code 不属于你的 AppID），要做登录就必须用自己的小程序 AppID
- 若项目已导入过：改完 `project.config.json` 的 `appid` 后，需在开发者工具「详情 → 基本信息 → AppID」重新设置或关项目重开，光点编译不会重载 appid
- 排错已经内置：小程序登录时会把 `wx.getAccountInfoSync()` 拿到的真实 AppID 一起上报，后端与自己的 `WECHAT_APPID` 比对，不一致就直接回 `400 AppID 不一致：小程序侧 wxA，后端 WECHAT_APPID wxB`，弹窗里两个值一目了然。另外 `GET /api/health` 会回报 `wechat_login`（`prod`/`dev`）和后端当前的 `appid`（AppID 是公开信息，不是密钥），不用登后台就能确认环境变量生效没有

### 2.1 登录后首页空白 / 控制台报 401 的排错顺序
| 现象 | 原因 | 处理 |
|---|---|---|
| `GET /api/group 401`，随后自动恢复 | 后端重启/重新部署把 SQLite 清了，本地存的旧 token 对应的人已不存在 | 正常，`utils/request.js` 会丢旧 token、静默重登并重试一次 |
| 弹窗「AppID 不一致：小程序侧 wxA，后端 WECHAT_APPID wxB」 | 开发者工具还在用旧/别的 AppID（改了 `project.config.json` 没重开项目最常见） | 按弹窗提示对齐：改后端两个变量，或改 `project.config.json` 后关项目重开 |
| `POST /api/auth/login 400`，`errcode=40029`（且没报"AppID 不一致"，即两侧 AppID 相同） | code 与 AppID 不匹配：① 用的是**公众号测试号**的 AppID（`/debug/cgi-bin/sandbox` 那个页面）而不是小程序的；② 开发者工具用游客模式/别人账号登录，code 不属于该 AppID；③ code 被用过第二次或超 5 分钟 | 按 §二.1 注册小程序账号并替换两处凭据；开发者工具用该小程序管理员微信号登录 |
| `POST /api/auth/login 400`，`errcode=40013` | 后端 `WECHAT_APPID` 本身微信不认（抄错/不存在） | 核对 AppID；`GET /api/health` 能看后端当前值 |
| `POST /api/auth/login 400`，`errcode=40125` | `WECHAT_SECRET` 与该 appid 不配对（测试号重置过密码） | 重新抄 AppSecret 更新 Render 环境变量并重新部署 |
| `errcode=40164` IP 不在白名单 | 微信侧要求配 IP 白名单 | 实测 Render 新加坡出口 IP **不会**触发；若换到别家平台遇到，去后台取消 IP 白名单限制 |
| 请求直接 fail、无状态码 | 未勾「不校验合法域名」或后端在休眠 | 本地设置勾上；先访问 `/api/health` 唤醒 |

> 错误码判读：`40013`=appid 不存在、`40125`=appid 与 secret 不配对、`40164`=调用方 IP 不在白名单、`40029`=code 无效。**能走到 `40029` 只说明这对 appid+secret 是真实配对的，并不说明它是"小程序"账号** —— 公众号测试号的一对凭据在这一步同样能通过校验，但它永远换不出小程序的 code（本项目就是这么踩的坑）。判定账号类型用 §二.1 那两条只读调用。

### 3. 指向后端
- 改 `miniprogram/config.js` 的 `BASE_URL`：本地联调 `http://127.0.0.1:8000`；部署后 `https://badminton-api-5k6c.onrender.com`
- 本地联调需在开发者工具"详情→本地设置"勾选 **不校验合法域名**

### 4. 域名白名单（个人/正式小程序必做）
- 小程序后台 →「开发管理 → 开发设置 → 服务器域名」→ **request 合法域名** 与 **uploadFile 合法域名** 都加 `https://badminton-api-5k6c.onrender.com`（每月有修改次数限制，一次填对）
- 域名必须 HTTPS 且备案可达；Render 的 `*.onrender.com` 实测在开发者工具勾「不校验合法域名」后可通，真机则以上面白名单为准
- 只改后端代码不涉及域名时，无需重新配置这里

### 5. 群友怎么打开
- 开发者工具「预览」出二维码：**扫码者需是该小程序的项目成员或体验成员**，且预览码有时效，适合自己调试，不适合发群里
- 给群友用的两条路：
  1. 「上传」代码 → 后台「版本管理」里设为**体验版** → 把群友加成**体验成员**（个人主体成员数量有上限，几十人可能加不全）；体验版不需审核
  2. **正式发布**：提交审核（本小程序只做内部记账、无支付、无 UGC 公开社区，一般按"工具/生活服务"类目可过），通过后任何人可搜索打开，人数不受体验名单限制
- 无论哪条路，先按 §4 配好服务器域名，否则真机请求会被微信拦下

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
