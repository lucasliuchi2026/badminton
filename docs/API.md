# 打球吗 API 文档

Base URL：本地 `http://127.0.0.1:8000`，部署后 `https://badminton-api-5k6c.onrender.com`

- 除 `/api/auth/login`、`/api/health` 外，所有接口需请求头 `Authorization: Bearer <token>`
- `GET /api/health` → `{ "ok": true, "app": "badminton-api", "wechat_login": "prod|dev", "appid": "后端 WECHAT_APPID" }`（`dev`=未配微信凭据，用假 code 也能登录；AppID 是公开信息）
- 统一错误格式：`{"detail": "错误原因"}`，状态码 400（业务校验）/ 401（未登录）/ 403（非群主）/ 404
- 点卡为**内部记账积分，无真实资金**

## 1. 登录 / 用户

### POST /api/auth/login
入参：
```json
{ "code": "wx.login返回的code", "appid": "小程序当前AppID(可选，仅用于与后端比对排错)",
  "nickname": "张三(可选)", "gender": "M(可选)", "avatar": "(可选)" }
```
- 传了 `appid` 且与后端 `WECHAT_APPID` 不同 → `400 {"detail":"AppID 不一致：小程序侧 wxA，后端 WECHAT_APPID wxB"}`（不再让微信只回一个看不懂的 40029）
返回（**第一个登录的用户自动成为群主 owner**，其余为 member）：
```json
{ "token": "eyJhb...", "user": { "id": 1, "openid": "dev-xxx", "nickname": "张三",
  "avatar": "", "gender": "M", "role": "owner", "card_balance": 0 } }
```
> 未配置 WECHAT_APPID 时后端进入 dev 模式：openid = "dev-"+code，无需微信服务器即可联调。

### GET /api/auth/me → 当前用户对象（同上 user 字段）

### POST /api/auth/profile
入参 `{ "nickname": "新昵称", "gender": "F", "avatar": "url" }`（字段可省略）→ 返回更新后的 user。

### POST /api/auth/avatar （multipart/form-data）
表单字段 `file`（≤2MB，chooseAvatar 临时图片）→ 返回更新后的 user，`avatar` 为 `/uploads/avatar_<id>_xxx.png`，前端拼 BASE_URL 访问。

## 2. 活动

### GET /api/activities?scope=active|history&keyword=
`scope=active` 广场（未结束），`scope=history` 历史；keyword 按名称/场地模糊过滤。返回：
```json
[ { "id": 1, "name": "周六晚双打局", "venue": "奥体中心 3-5号场", "date": "2026-10-04",
    "time_start": "19:00", "time_end": "21:00", "type": "paid", "cost_m": 30, "cost_f": 20,
    "cap_m": 6, "cap_f": 4, "status": "upcoming",
    "signed_m": 3, "signed_f": 2, "signed_total": 5 } ]
```
`type`: `free` 仅报名 / `paid` 积分预付（`cost_m`/`cost_f` 为男女各自每人消耗积分）。
`status`: `upcoming/ongoing/ended/cancelled`。

### GET /api/activities/{id}
同上并追加明细：
```json
{ "registrations_m": [ { "id": 11, "member_name": "张三", "paid": 30, "creator_id": 1, "is_self": true } ],
  "registrations_f": [], "media": [ { "id": 3, "kind": "photo", "url": "/uploads/1_ab12.jpg" } ] }
```

### POST /api/activities 🔒群主
入参：
```json
{ "name": "周六晚双打局", "venue": "奥体中心", "date": "2026-10-04", "time_start": "19:00",
  "time_end": "21:00", "type": "paid", "cost_m": 30, "cost_f": 20, "cap_m": 6, "cap_f": 4 }
```
→ 返回活动对象。成员调用返回 403。

### PUT /api/activities/{id} 🔒群主（入参同 POST）
### POST /api/activities/{id}/status 🔒群主
入参 `{ "status": "ongoing" }`（upcoming/ongoing/ended/cancelled）。

## 3. 报名

### POST /api/activities/{id}/signup （所有已登录用户）
入参 `{ "gender": "M", "slots": 3, "names": ["小明", "小红"] }`
- `gender` 占用哪个性别名额；`slots` 含本人；`names` 代报昵称，数量必须 = slots-1
- 积分局(paid)：从**操作人**点卡扣 `单价×slots`（余额不足 400：`点卡余额不足...`）；免费局不扣
- 名额超了 400：`男生名额不足：剩余 N 个`；活动已结束 400
返回：
```json
{ "created": 3, "activity": { ...同活动对象... } }
```

### POST /api/activities/registrations/{reg_id}/cancel （本人发起的报名或群主）
活动 `upcoming` 时取消按名额单价退还给付款人（biz=refund）。

### GET /api/activities/mine/registrations
我报名/代报参与过的活动列表（个人中心）：
```json
[ { "activity_id": 1, "name": "周六晚双打局", "date": "2026-10-04", "time_start": "19:00",
    "venue": "奥体中心", "status": "upcoming", "paid": 30 } ]
```

## 4. 素材

### POST /api/activities/{id}/media （multipart/form-data，所有成员）
表单字段：`file`（≤20MB）、`kind`（photo/video）
返回 `{ "id": 3, "kind": "photo", "url": "/uploads/1_ab12cd34.jpg", "size": 204800 }`
前端拼 `BASE_URL + url` 访问。

### GET /api/activities/{id}/review （回顾文案占位，后续可接大模型不改接口）
```json
{ "activity_id": 1, "text": "【活动回顾】... 无羽伦比，扣杀生活——下次球场见！", "engine": "template" }
```

## 5. 积分赛

### GET /api/league/standings 排行榜（points 降序）
```json
[ { "user_id": 2, "nickname": "李四", "gender": "M", "points": 120, "wins": 5, "losses": 1 } ]
```

### GET /api/league/matches 历史对局
```json
[ { "id": 2, "date": "2026-09-27", "a": "李四", "b": "张三", "score_a": 2, "score_b": 1,
    "detail": "21-15, 18-21, 21-13" } ]
```

### POST /api/league/matches 🔒群主
入参 `{ "player_a_id": 2, "player_b_id": 1, "score_a": 2, "score_b": 1,
"detail": "21-15, 18-21, 21-13", "played_at": "2026-10-01", "activity_id": null }`
- 校验：不同人、分不出平局 400、局数 0-3 且分差≤2
- **自动结算**：胜方 +25 分、负方 +5 分（standings 同事务更新）
返回 `{ "id": 3, "ok": true }`

## 6. 点卡（内部记账）

### GET /api/cards/mine 本人余额+流水
```json
{ "card_balance": 70, "logs": [ { "id": 5, "delta": -30, "balance_after": 70,
  "memo": "「周六晚双打局」报名预付积分 ×1人（♂30分/人）", "biz": "signup", "created_at": "2026-10-01 21:30" } ] }
```
`biz`: signup 报名扣分 / refund 取消退还 / adjust 群主调整。

### GET /api/cards/logs?user_id=N 指定成员流水（普通成员仅能查自己，否则 403）
### GET /api/cards/users 🔒群主 全员余额一览
### POST /api/cards/adjust 🔒群主
入参 `{ "user_id": 2, "delta": 50, "memo": "国庆场地费AA多退" }`（delta≠0，不允许扣成负数）
返回 `{ "ok": true, "user_id": 2, "card_balance": 110, "log": {...} }`

## 7. 群配置 / 其他

### GET /api/group 首页 Hero（club_name/slogan/intro，未设置时返回内置默认值）
### PUT /api/group 🔒群主 入参 `{ "slogan": "无羽伦比，扣杀生活！" }`（字段可省略）
### GET /api/users 成员基础列表（选人用，不含余额）
### GET /api/health（见文首：探活 + 回报微信登录模式与后端 AppID，Render 健康检查也用它）
