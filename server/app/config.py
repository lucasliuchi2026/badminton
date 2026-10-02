import os


class Settings:
    """运行配置：全部来自环境变量，本地开发用默认值即可跑"""

    SECRET_KEY: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    WECHAT_APPID: str = os.getenv("WECHAT_APPID", "")
    WECHAT_SECRET: str = os.getenv("WECHAT_SECRET", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./badminton.db")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    TOKEN_HOURS: int = 24 * 30
    # 积分结算规则（与产品约定一致：胜 +25 / 负 +5）
    WIN_POINTS: int = 25
    LOSE_POINTS: int = 5


settings = Settings()
