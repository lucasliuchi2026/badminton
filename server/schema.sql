-- ============================================================
-- 打球吗 · 建表 SQL（SQLite 方言，Postgres 仅需把 INTEGER PRIMARY KEY AUTOINCREMENT 改为 SERIAL）
-- 由应用启动时 SQLAlchemy 自动建表，本文件供查阅 / 手动初始化
-- 点卡为内部记账，无真实资金
-- ============================================================

-- 用户表：openid 唯一；role: owner(群主) / member(普通成员)
-- 说明：首个登录的用户自动成为群主（单群模式，见 app/routers/auth.py）
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    openid        VARCHAR(64) NOT NULL UNIQUE,
    nickname      VARCHAR(32) NOT NULL DEFAULT '球友',
    avatar        VARCHAR(255) NOT NULL DEFAULT '',
    gender        CHAR(1) NOT NULL DEFAULT 'M',          -- M / F
    role          VARCHAR(10) NOT NULL DEFAULT 'member', -- owner / member
    card_balance  INTEGER NOT NULL DEFAULT 0,            -- 点卡余额（冗余列，每次变动必写 card_logs）
    created_at    DATETIME
);

-- 活动表：type=free 仅报名 / paid 积分预付（男女消耗可不同）；status 由群主流转
CREATE TABLE IF NOT EXISTS activities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(64) NOT NULL,
    venue       VARCHAR(128) NOT NULL,
    date        VARCHAR(10) NOT NULL,                    -- YYYY-MM-DD
    time_start  VARCHAR(5) NOT NULL,                     -- HH:MM
    time_end    VARCHAR(5) NOT NULL,
    type        VARCHAR(10) NOT NULL DEFAULT 'free',     -- free / paid
    cost_m      INTEGER NOT NULL DEFAULT 0,              -- 男生报名消耗积分（点卡/人）
    cost_f      INTEGER NOT NULL DEFAULT 0,              -- 女生报名消耗积分（点卡/人）
    cap_m       INTEGER NOT NULL DEFAULT 0,              -- 男生名额
    cap_f       INTEGER NOT NULL DEFAULT 0,              -- 女生名额
    status      VARCHAR(10) NOT NULL DEFAULT 'upcoming', -- upcoming / ongoing / ended / cancelled
    created_by  INTEGER NOT NULL REFERENCES users(id),
    created_at  DATETIME
);

-- 报名表：一行 = 一个参与名额；creator 为操作人（本人或代报人），paid 记录该名额实扣积分
CREATE TABLE IF NOT EXISTS registrations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id  INTEGER NOT NULL REFERENCES activities(id),
    creator_id   INTEGER NOT NULL REFERENCES users(id),   -- 谁操作报名（代报时积分从此人点卡扣）
    member_id    INTEGER REFERENCES users(id),             -- 已知群成员则关联；代报新人可空
    member_name  VARCHAR(32) NOT NULL,                     -- 名单显示名
    gender       CHAR(1) NOT NULL,                         -- 占用的名额性别 M / F
    paid         INTEGER NOT NULL DEFAULT 0,               -- 本名额扣减的积分
    status       VARCHAR(10) NOT NULL DEFAULT 'active',    -- active / cancelled
    created_at   DATETIME
);
CREATE INDEX IF NOT EXISTS idx_reg_activity ON registrations(activity_id, status);

-- 对局记录表：积分赛只记局分（小分存 detail 文本）
CREATE TABLE IF NOT EXISTS matches (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id  INTEGER REFERENCES activities(id),        -- 可空：脱场对局
    player_a_id  INTEGER NOT NULL REFERENCES users(id),
    player_b_id  INTEGER NOT NULL REFERENCES users(id),
    score_a      INTEGER NOT NULL,                         -- A 胜局数
    score_b      INTEGER NOT NULL,
    detail       VARCHAR(128) NOT NULL DEFAULT '',         -- 如 "21-15, 18-21, 21-13"
    played_at    VARCHAR(10) NOT NULL,                     -- YYYY-MM-DD
    recorded_by  INTEGER NOT NULL REFERENCES users(id),    -- 录分人（群主）
    created_at   DATETIME
);

-- 积分表：由对局录入时原子更新（胜 +25 / 负 +5），可随时由 matches 重算校验
CREATE TABLE IF NOT EXISTS standings (
    user_id  INTEGER PRIMARY KEY REFERENCES users(id),
    points   INTEGER NOT NULL DEFAULT 0,
    wins     INTEGER NOT NULL DEFAULT 0,
    losses   INTEGER NOT NULL DEFAULT 0
);

-- 点卡流水表：只增不改；biz 区分场景便于审计
CREATE TABLE IF NOT EXISTS card_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id),
    delta          INTEGER NOT NULL,                       -- 正=记分 负=扣减
    balance_after  INTEGER NOT NULL,                       -- 变更后余额快照
    memo           VARCHAR(128) NOT NULL,
    biz            VARCHAR(16) NOT NULL,                   -- signup / refund / adjust
    operator_id    INTEGER NOT NULL REFERENCES users(id),  -- 群主调整时=群主；报名扣分时=本人
    created_at     DATETIME
);
CREATE INDEX IF NOT EXISTS idx_cardlog_user ON card_logs(user_id, created_at);

-- 活动素材表：照片/短视频，文件存 UPLOAD_DIR，url 为相对访问路径
CREATE TABLE IF NOT EXISTS media (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id  INTEGER NOT NULL REFERENCES activities(id),
    uploader_id  INTEGER NOT NULL REFERENCES users(id),
    kind         VARCHAR(8) NOT NULL,                      -- photo / video
    url          VARCHAR(255) NOT NULL,
    size         INTEGER NOT NULL DEFAULT 0,
    created_at   DATETIME
);

-- 群配置表（键值）：单群模式，存群名/slogan/介绍，群主可改
CREATE TABLE IF NOT EXISTS group_config (
    key    VARCHAR(32) PRIMARY KEY,
    value  TEXT NOT NULL
);
