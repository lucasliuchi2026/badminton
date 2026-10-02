import httpx

from .config import settings

_CODE2SESSION_PATH = "/sns/jscode2session"


async def code_to_openid(code: str) -> str:
    """微信登录凭证换 openid；未配置 AppID 时进入 dev 模式（本地/测试直接放行）"""
    if not settings.WECHAT_APPID:
        return "dev-" + code  # 开发模式：以 code 为稳定身份，方便无微信环境联调
    url = settings.WECHAT_API_BASE + _CODE2SESSION_PATH
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                url,
                params={
                    "appid": settings.WECHAT_APPID,
                    "secret": settings.WECHAT_SECRET,
                    "js_code": code,
                    "grant_type": "authorization_code",
                },
            )
            data = resp.json()
    except Exception as e:
        # 连不上/超时/非 json 响应都会到这里；不包成 400 就只剩一个没有信息的 500
        raise ValueError(f"调微信接口失败 {type(e).__name__}: {e}（接口 {url}）")
    if "openid" not in data:
        raise ValueError(f"微信登录失败: {data.get('errmsg', 'unknown')} (errcode={data.get('errcode')})")
    return data["openid"]
