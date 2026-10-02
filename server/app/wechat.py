import httpx

from .config import settings

_CODE2SESSION = "https://api.weixin.qq.com/sns/jscode2session"


async def code_to_openid(code: str) -> str:
    """微信登录凭证换 openid；未配置 AppID 时进入 dev 模式（本地/测试直接放行）"""
    if not settings.WECHAT_APPID:
        return "dev-" + code  # 开发模式：以 code 为稳定身份，方便无微信环境联调
    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(
            _CODE2SESSION,
            params={
                "appid": settings.WECHAT_APPID,
                "secret": settings.WECHAT_SECRET,
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
        data = resp.json()
    if "openid" not in data:
        raise ValueError(f"微信登录失败: {data.get('errmsg', 'unknown')} (errcode={data.get('errcode')})")
    return data["openid"]
