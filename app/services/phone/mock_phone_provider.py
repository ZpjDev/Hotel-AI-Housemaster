import logging
import json
import time
from typing import Dict
from app.services.phone.phone_base import PhoneProviderBase
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class MockPhoneProvider(PhoneProviderBase):
    """Mock 电话 Provider - Phase 1"""

    async def handle_inbound_call(self, payload: Dict) -> Dict:
        start = time.time()
        try:
            result = {
                "status": "ok",
                "call_id": "mock_call_001",
                "transcript": payload.get("transcript", "您好，请问有什么可以帮您？"),
                "action": "answered",
            }
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_phone_provider", "/handle_inbound_call",
                request_data=json.dumps(payload, ensure_ascii=False)[:500],
                response_data=json.dumps(result, ensure_ascii=False),
                success=True, latency_ms=round(latency, 2),
            )
            return result
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_phone_provider", "/handle_inbound_call",
                success=False, error_message=str(e), latency_ms=round(latency, 2),
            )
            return {"status": "error", "message": str(e)}

    async def transcribe_call(self, audio_url: str) -> str:
        start = time.time()
        try:
            result = "Mock 转写文本：客户咨询房型和价格"
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_phone_provider", "/transcribe_call",
                request_data=f'{{"audio_url":"{audio_url}"}}',
                response_data=f'{{"text":"{result}"}}',
                success=True, latency_ms=round(latency, 2),
            )
            return result
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_phone_provider", "/transcribe_call",
                success=False, error_message=str(e), latency_ms=round(latency, 2),
            )
            raise

    async def answer_question(self, call_text: str, hotel_id: int) -> str:
        start = time.time()
        try:
            result = f"Mock AI 回复：您好！关于您的问题「{call_text}」，我们的客服会为您解答。"
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_phone_provider", "/answer_question",
                request_data=f'{{"call_text":"{call_text[:50]}","hotel_id":{hotel_id}}}',
                response_data=f'{{"answer":"{result[:50]}"}}',
                success=True, latency_ms=round(latency, 2),
            )
            return result
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_phone_provider", "/answer_question",
                success=False, error_message=str(e), latency_ms=round(latency, 2),
            )
            raise

    async def transfer_to_human(self, reason: str) -> Dict:
        start = time.time()
        try:
            result = {"status": "ok", "message": f"已转人工处理，原因: {reason}"}
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_phone_provider", "/transfer_to_human",
                request_data=f'{{"reason":"{reason}"}}',
                response_data=json.dumps(result, ensure_ascii=False),
                success=True, latency_ms=round(latency, 2),
            )
            return result
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_phone_provider", "/transfer_to_human",
                success=False, error_message=str(e), latency_ms=round(latency, 2),
            )
            return {"status": "error", "message": str(e)}

    async def test_connection(self) -> Dict:
        return {"status": "ok", "message": "Mock Phone Provider 可用"}

    def get_provider_name(self) -> str:
        return "mock_phone_provider"
