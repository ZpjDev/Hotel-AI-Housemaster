import logging
import time
from typing import Dict
from app.config import settings
from app.services.phone.phone_base import PhoneProviderBase
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class TencentPhoneProvider(PhoneProviderBase):
    """腾讯云语音 Provider - 预留接口"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.PHONE_API_KEY

    async def handle_inbound_call(self, payload: Dict) -> Dict:
        if not self.api_key:
            from app.services.phone.mock_phone_provider import MockPhoneProvider
            return await MockPhoneProvider().handle_inbound_call(payload)
        start_time = time.time()
        try:
            logger.info(f"[TencentPhoneProvider] 处理来电")
            result = {"status": "ok", "message": "腾讯云语音接口预留"}
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="tencent_phone_provider",
                endpoint="handle_inbound_call",
                request_data={"payload_keys": list(payload.keys())},
                response_data=result,
                success=True,
                latency_ms=latency,
            )
            return result
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="tencent_phone_provider",
                endpoint="handle_inbound_call",
                request_data={"payload_keys": list(payload.keys())},
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            raise

    async def transcribe_call(self, audio_url: str) -> str:
        if not self.api_key:
            from app.services.phone.mock_phone_provider import MockPhoneProvider
            return await MockPhoneProvider().transcribe_call(audio_url)
        start_time = time.time()
        try:
            result = "腾讯云语音转写结果（预留）"
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="tencent_phone_provider",
                endpoint="transcribe_call",
                request_data={"audio_url": audio_url},
                response_data={"transcript_length": len(result)},
                success=True,
                latency_ms=latency,
            )
            return result
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="tencent_phone_provider",
                endpoint="transcribe_call",
                request_data={"audio_url": audio_url},
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            raise

    async def answer_question(self, call_text: str, hotel_id: int) -> str:
        if not self.api_key:
            from app.services.phone.mock_phone_provider import MockPhoneProvider
            return await MockPhoneProvider().answer_question(call_text, hotel_id)
        start_time = time.time()
        try:
            result = "腾讯云 AI 语音回答（预留）"
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="tencent_phone_provider",
                endpoint="answer_question",
                request_data={"call_text": call_text, "hotel_id": hotel_id},
                response_data={"answer_length": len(result)},
                success=True,
                latency_ms=latency,
            )
            return result
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="tencent_phone_provider",
                endpoint="answer_question",
                request_data={"call_text": call_text, "hotel_id": hotel_id},
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            raise

    async def transfer_to_human(self, reason: str) -> Dict:
        start_time = time.time()
        try:
            logger.info(f"[TencentPhoneProvider] 转人工: {reason}")
            result = {"status": "ok", "message": "已转人工处理"}
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="tencent_phone_provider",
                endpoint="transfer_to_human",
                request_data={"reason": reason},
                response_data=result,
                success=True,
                latency_ms=latency,
            )
            return result
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="tencent_phone_provider",
                endpoint="transfer_to_human",
                request_data={"reason": reason},
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            raise

    async def test_connection(self) -> Dict:
        if not self.api_key:
            return {"status": "mock", "message": "未配置腾讯云 API Key，使用 Mock 模式"}
        return {"status": "ok", "message": "腾讯云语音 API 已配置"}

    def get_provider_name(self) -> str:
        return "tencent_phone_provider"
