import logging
import hashlib
import json
import time
from typing import Dict, Optional
from app.services.external_api.base_provider import WechatProvider
from app.services.ai_provider import get_wechat_config
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class MockWechatProvider(WechatProvider):
    """Mock 微信 Provider"""

    async def send_message(self, openid: str, message: str) -> Dict:
        start = time.time()
        try:
            logger.info(f"[MockWechatProvider] 发送消息给 {openid}: {message[:50]}...")
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_wechat_provider", "/message/send",
                request_data=json.dumps({"openid": openid, "message": message[:100]}, ensure_ascii=False),
                response_data='{"status":"ok"}',
                success=True, latency_ms=round(latency, 2),
            )
            return {"status": "ok", "message": "Mock 消息已发送"}
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_wechat_provider", "/message/send",
                success=False, error_message=str(e), latency_ms=round(latency, 2),
            )
            return {"status": "error", "message": str(e)}

    async def parse_message(self, payload: Dict) -> Dict:
        return {
            "openid": payload.get("FromUserName", payload.get("openid", "")),
            "message": payload.get("Content", payload.get("message", "")),
            "msg_type": payload.get("MsgType", "text"),
        }

    async def test_connection(self) -> Dict:
        return {"status": "ok", "message": "Mock Wechat Provider 可用"}

    def get_provider_name(self) -> str:
        return "mock_wechat_provider"


class OfficialWechatProvider(WechatProvider):
    """微信公众号/企业微信 Provider"""

    _access_token: str = ""
    _access_token_expires_at: float = 0.0

    def __init__(self, app_id: str = "", app_secret: str = "", token: str = "", encoding_aes_key: str = ""):
        wc = get_wechat_config()
        self.app_id = app_id or wc.get("app_id", "")
        self.app_secret = app_secret or wc.get("app_secret", "")
        self.token = token or wc.get("token", "")
        self.encoding_aes_key = encoding_aes_key or wc.get("encoding_aes_key", "")

    def verify_signature(self, timestamp: str, nonce: str, signature: str) -> bool:
        """验证微信签名"""
        if not self.token:
            return True
        tmp_list = [self.token, timestamp, nonce]
        tmp_list.sort()
        tmp_str = "".join(tmp_list)
        hash_str = hashlib.sha1(tmp_str.encode("utf-8")).hexdigest()
        return hash_str == signature

    async def send_message(self, openid: str, message: str) -> Dict:
        start = time.time()
        if not self.app_id or not self.app_secret:
            mock = MockWechatProvider()
            return await mock.send_message(openid, message)

        try:
            import httpx
            access_token = await self.get_access_token()
            async with httpx.AsyncClient(timeout=10.0) as client:
                send_url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"
                resp = await client.post(
                    send_url,
                    json={
                        "touser": openid,
                        "msgtype": "text",
                        "text": {"content": message},
                    },
                )
                latency = (time.time() - start) * 1000
                data = resp.json()
                success = resp.status_code == 200 and data.get("errcode", 0) == 0
                log_api_call(
                    "official_wechat_provider", "/cgi-bin/message/custom/send",
                    request_data=json.dumps({"touser": openid}, ensure_ascii=False),
                    response_data=resp.text[:500],
                    success=success,
                    error_message=None if success else resp.text[:200],
                    latency_ms=round(latency, 2),
                )
                return data
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                "official_wechat_provider", "/message/send",
                success=False, error_message=str(e), latency_ms=round(latency, 2),
            )
            return {"status": "error", "message": str(e)}

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """获取并缓存微信公众号 access_token。"""
        now = time.time()
        if (
            not force_refresh
            and self.__class__._access_token
            and self.__class__._access_token_expires_at > now + 60
        ):
            return self.__class__._access_token

        if not self.app_id or not self.app_secret:
            raise ValueError("微信 AppID/AppSecret 未配置")

        import httpx
        start = time.time()
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)

        latency = (time.time() - start) * 1000
        data = resp.json()
        access_token = data.get("access_token")
        if resp.status_code != 200 or not access_token:
            log_api_call(
                "official_wechat_provider", "/cgi-bin/token",
                request_data=json.dumps({"appid": self.app_id}, ensure_ascii=False),
                response_data=resp.text[:500],
                success=False,
                error_message=resp.text[:200],
                latency_ms=round(latency, 2),
            )
            raise RuntimeError(data.get("errmsg") or "获取微信 access_token 失败")

        expires_in = int(data.get("expires_in", 7200))
        self.__class__._access_token = access_token
        self.__class__._access_token_expires_at = now + max(expires_in - 300, 60)
        log_api_call(
            "official_wechat_provider", "/cgi-bin/token",
            request_data=json.dumps({"appid": self.app_id}, ensure_ascii=False),
            response_data=json.dumps({"expires_in": expires_in}, ensure_ascii=False),
            success=True,
            latency_ms=round(latency, 2),
        )
        return access_token

    async def parse_message(self, payload: Dict) -> Dict:
        if payload.get("MsgType") == "text":
            return {
                "openid": payload.get("FromUserName", ""),
                "message": payload.get("Content", ""),
                "msg_type": "text",
            }
        return {
            "openid": payload.get("FromUserName", ""),
            "message": "",
            "msg_type": payload.get("MsgType", "unknown"),
        }

    async def test_connection(self) -> Dict:
        if not self.app_id or not self.app_secret:
            return {"status": "mock", "message": "未配置微信 AppID/AppSecret，使用 Mock 模式"}
        try:
            await self.get_access_token(force_refresh=True)
            return {"status": "ok", "message": "微信 access_token 获取成功"}
        except Exception as e:
            return {"status": "error", "message": f"微信 API 连接失败: {e}"}

    def get_provider_name(self) -> str:
        return "official_wechat_provider"


def get_wechat_provider(config: Optional[Dict] = None) -> WechatProvider:
    """获取微信 Provider，自动降级到 Mock"""
    if config:
        app_id = config.get("app_id", "")
        app_secret = config.get("app_secret", "")
        token = config.get("token", "")
        encoding_aes_key = config.get("encoding_aes_key", "")
    else:
        wc = get_wechat_config()
        app_id = wc.get("app_id", "")
        app_secret = wc.get("app_secret", "")
        token = wc.get("token", "")
        encoding_aes_key = wc.get("encoding_aes_key", "")

    if token or (app_id and app_secret):
        return OfficialWechatProvider(
            app_id=app_id,
            app_secret=app_secret,
            token=token,
            encoding_aes_key=encoding_aes_key,
        )
    return MockWechatProvider()
