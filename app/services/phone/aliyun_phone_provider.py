import logging
import json
import time
from typing import Dict
from app.config import settings
from app.services.phone.phone_base import PhoneProviderBase
from app.services.ai_provider import get_phone_config
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class AliyunPhoneProvider(PhoneProviderBase):
    """阿里云语音 Provider - 预留接口"""

    def __init__(self, api_key: str = None):
        pc = get_phone_config()
        self.api_key = api_key or pc.get("api_key", "")

    async def handle_inbound_call(self, payload: Dict) -> Dict:
        start = time.time()
        if not self.api_key:
            from app.services.phone.mock_phone_provider import MockPhoneProvider
            return await MockPhoneProvider().handle_inbound_call(payload)
        try:
            result = {"status": "ok", "message": "阿里云语音接口预留"}
            latency = (time.time() - start) * 1000
            log_api_call(
                "aliyun_phone_provider", "/handle_inbound_call",
                request_data=json.dumps(payload, ensure_ascii=False)[:200],
                response_data=json.dumps(result, ensure_ascii=False),
                success=True, latency_ms=round(latency, 2),
            )
            return result
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                "aliyun_phone_provider", "/handle_inbound_call",
                success=False, error_message=str(e), latency_ms=round(latency, 2),
            )
            raise

    async def transcribe_call(self, audio_url: str) -> str:
        start = time.time()
        if not self.api_key:
            from app.services.phone.mock_phone_provider import MockPhoneProvider
            return await MockPhoneProvider().transcribe_call(audio_url)
        result = "阿里云语音转写结果（预留）"
        latency = (time.time() - start) * 1000
        log_api_call(
            "aliyun_phone_provider", "/transcribe_call",
            request_data=f'{{"audio_url":"{audio_url}"}}',
            success=True, latency_ms=round(latency, 2),
        )
        return result

    async def answer_question(self, call_text: str, hotel_id: int) -> str:
        if not self.api_key:
            from app.services.phone.mock_phone_provider import MockPhoneProvider
            return await MockPhoneProvider().answer_question(call_text, hotel_id)
        return "阿里云 AI 语音回答（预留）"

    async def transfer_to_human(self, reason: str) -> Dict:
        start = time.time()
        result = {"status": "ok", "message": "已转人工处理"}
        latency = (time.time() - start) * 1000
        log_api_call(
            "aliyun_phone_provider", "/transfer_to_human",
            request_data=f'{{"reason":"{reason}"}}',
            response_data=json.dumps(result, ensure_ascii=False),
            success=True, latency_ms=round(latency, 2),
        )
        return result

    async def test_connection(self) -> Dict:
        if not self.api_key:
            return {"status": "mock", "message": "未配置阿里云 API Key，使用 Mock 模式"}
        return {"status": "ok", "message": "阿里云语音 API 已配置"}

    def get_provider_name(self) -> str:
        return "aliyun_phone_provider"
