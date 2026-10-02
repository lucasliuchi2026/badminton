import os


class Settings:
    """运行配置：全部来自环境变量，本地开发用默认值即可跑"""

    SECRET_KEY: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    WECHAT_APPID: str = os.getenv("WECHAT_APPID", "")
    WECHAT_SECRET: str = os.getenv("WECHAT_SECRET", "")
    # 微信云托管内调开放接口走内网，官方建议直接用 http 且不带 access_token；
    # 本地/其它平台仍需 https 公网地址，故基址交给环境变量
    WECHAT_API_BASE: str = os.getenv("WECHAT_API_BASE", "https://api.weixin.qq.com")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./badminton.db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    TOKEN_HOURS: int = 24 * 30
    # 积分结算规则（与产品约定一致：胜 +25 / 负 +5）
    WIN_POINTS: int = 25
    LOSE_POINTS: int = 5


settings = Settings()
