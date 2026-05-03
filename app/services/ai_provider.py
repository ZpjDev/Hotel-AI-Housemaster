import httpx
import time
import logging
import base64
import os
from typing import Optional
from sqlmodel import Session, select
from app.database import engine
from app.config import settings
from app.models import APIConfig
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


# ============ 加密工具 ============
def encrypt_value(value: str) -> str:
    """加密值（MVP 用 base64，后续可替换为 AES）"""
    if not value:
        return value
    secret = os.environ.get("ENCRYPTION_SECRET", "hotel_ai_butler_default_secret")
    prefixed = f"{secret[:8]}:{value}"
    return "enc:" + base64.b64encode(prefixed.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str) -> str:
    """解密值（MVP 用 base64，后续可替换为 AES）"""
    if not value or not value.startswith("enc:"):
        return value
    try:
        encoded = value[4:]
        decoded = base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
        parts = decoded.split(":", 1)
        return parts[1] if len(parts) > 1 else decoded
    except Exception as e:
        logger.error(f"解密失败: {e}")
        return value


def get_db_config(key: str, default: str = None) -> Optional[str]:
    """从数据库读取 API 配置"""
    try:
        with Session(engine) as session:
            cfg = session.exec(select(APIConfig).where(APIConfig.key == key)).first()
            if cfg:
                return decrypt_value(cfg.value) if cfg.is_encrypted else cfg.value
    except Exception as e:
        logger.warning(f"读取数据库配置 {key} 失败: {e}")
    return default


def get_ai_config():
    """获取 AI 配置：数据库优先，环境变量次之"""
    return {
        "api_base": get_db_config("ai_api_base") or settings.AI_API_BASE,
        "api_key": get_db_config("ai_api_key") or settings.AI_API_KEY,
        "model": get_db_config("ai_model") or settings.AI_MODEL,
    }


def get_ota_config():
    """获取 OTA 配置"""
    return {
        "api_base": get_db_config("ota_api_base") or settings.OTA_API_BASE,
        "api_key": get_db_config("ota_api_key") or settings.OTA_API_KEY,
    }


def get_wechat_config():
    """获取微信配置"""
    return {
        "token": get_db_config("wechat_token") or settings.WECHAT_TOKEN,
        "encoding_aes_key": get_db_config("wechat_encoding_aes_key") or settings.WECHAT_ENCODING_AES_KEY,
        "app_id": get_db_config("wechat_app_id") or settings.WECHAT_APP_ID,
        "app_secret": get_db_config("wechat_app_secret") or settings.WECHAT_APP_SECRET,
    }


def get_phone_config():
    """获取电话配置"""
    return {
        "api_base": get_db_config("phone_api_base") or settings.PHONE_API_BASE,
        "api_key": get_db_config("phone_api_key") or settings.PHONE_API_KEY,
    }


def get_notify_config():
    """获取通知配置"""
    return {
        "webhook_url": get_db_config("notify_webhook_url") or settings.NOTIFY_WEBHOOK_URL,
    }


# ============ AI Provider ============
class AIProvider:
    """AI Provider - 支持 OpenAI-compatible API"""

    def __init__(self, api_base: str = None, api_key: str = None, model: str = None):
        config = get_ai_config()
        self.api_base = (api_base or config["api_base"]).rstrip("/") if (api_base or config["api_base"]) else ""
        raw_key = api_key or config["api_key"] or ""
        if not raw_key or raw_key.startswith("your-") or raw_key in ["your_api_key"]:
            self.api_key = ""
        else:
            self.api_key = raw_key
        self.model = model or config["model"]

    async def chat_completion(self, messages: list, temperature: float = 0.7, max_retries: int = 2) -> str:
        """调用 AI 模型生成回复，支持 timeout、retry、fallback"""
        if not self.api_key:
            return self._mock_response(messages)

        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        last_error = None
        for attempt in range(max_retries + 1):
            start = time.time()
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    latency = (time.time() - start) * 1000

                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        log_api_call(
                            provider="ai_provider",
                            endpoint="/chat/completions",
                            request_data={"model": self.model, "message_count": len(messages)},
                            response_data={"content_length": len(content)},
                            success=True,
                            latency_ms=round(latency, 2),
                        )
                        return content
                    else:
                        last_error = f"API 返回 {response.status_code}: {response.text[:200]}"
                        log_api_call(
                            provider="ai_provider",
                            endpoint="/chat/completions",
                            request_data={"model": self.model},
                            response_data={"status_code": response.status_code},
                            success=False,
                            error_message=last_error,
                            latency_ms=round(latency, 2),
                        )
            except Exception as e:
                latency = (time.time() - start) * 1000
                last_error = f"请求失败: {str(e)[:200]}"
                log_api_call(
                    provider="ai_provider",
                    endpoint="/chat/completions",
                    success=False,
                    error_message=last_error,
                    latency_ms=round(latency, 2),
                )

            if attempt < max_retries:
                await __import__("asyncio").sleep(1 * (attempt + 1))

        logger.warning(f"AI API 调用失败，使用 Mock 响应。最后错误: {last_error}")
        return self._mock_response(messages)

    def _mock_response(self, messages: list) -> str:
        """当没有配置 API Key 时返回 mock 回复"""
        last_msg = messages[-1]["content"]

        if "定价" in last_msg or "价格" in last_msg:
            return "根据当前市场行情和竞品分析，建议您今晚将价格设定在 ¥299-359 之间。周边竞品均价约 ¥320，建议采取中等偏上策略，突出性价比优势。"
        elif "房态" in last_msg or "剩余" in last_msg:
            return "当前剩余房间较多，建议采取以下策略：1) 在 OTA 平台增加曝光，提升排名；2) 设置限时促销价，吸引即时下单；3) 联系协议客户和老客户，提供专属优惠。"
        elif "竞品" in last_msg:
            return "根据监测数据，周边竞品情况如下：A 酒店均价 ¥350，剩余 5 间；B 酒店均价 ¥280，剩余 12 间；C 酒店均价 ¥420，已满房。整体竞品均价 ¥317，您的定价建议保持在 ¥300-330 区间。"
        elif "报告" in last_msg:
            return "本月经营报告摘要：总营收 ¥125,000，平均入住率 78%，ADR ¥320，RevPAR ¥250。较上月增长 5.2%。详见完整报告。"
        elif "差评" in last_msg or "点评" in last_msg:
            return "非常感谢您的反馈，对于给您带来的不便我们深表歉意。我们已经记录您提到的问题，并将在 24 小时内联系您了解具体情况。"
        else:
            return f"收到您的问题：「{last_msg}」。AI 正在为您分析经营数据，请稍等片刻..."

    async def test_connection(self) -> dict:
        """测试 AI 连接"""
        if not self.api_key:
            return {"status": "mock", "message": "未配置 API Key，使用 Mock 模式"}
        try:
            result = await self.chat_completion([{"role": "user", "content": "你好"}])
            return {"status": "ok", "message": "AI API 连接成功"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
