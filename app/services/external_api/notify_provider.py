import logging
import time
from typing import Dict
from app.services.external_api.base_provider import NotifyProvider
from app.config import settings
from app.services.ai_provider import get_notify_config
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class MockNotifyProvider(NotifyProvider):
    """Mock 通知 Provider"""

    async def send_notification(self, target: str, message: str, channel: str = "webhook") -> Dict:
        start_time = time.time()
        try:
            logger.info(f"[MockNotifyProvider] 发送通知到 {target}: {message}")
            result = {"status": "ok", "message": f"通知已发送至 {target}"}
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="mock_notify_provider",
                endpoint="send_notification",
                request_data={"target": target, "message": message, "channel": channel},
                response_data=result,
                success=True,
                latency_ms=latency,
            )
            return result
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="mock_notify_provider",
                endpoint="send_notification",
                request_data={"target": target, "message": message, "channel": channel},
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            raise

    async def test_connection(self) -> Dict:
        return {"status": "ok", "message": "Mock Notify Provider 可用"}

    def get_provider_name(self) -> str:
        return "mock_notify_provider"


class WebhookNotifyProvider(NotifyProvider):
    """Webhook 通知 Provider"""

    def __init__(self, webhook_url: str = None):
        notify_config = get_notify_config()
        self.webhook_url = webhook_url or notify_config["webhook_url"] or settings.NOTIFY_WEBHOOK_URL

    async def send_notification(self, target: str, message: str, channel: str = "webhook") -> Dict:
        if not self.webhook_url:
            mock = MockNotifyProvider()
            return await mock.send_notification(target, message, channel)

        start_time = time.time()
        request_data = {"target": target, "message": message, "channel": channel, "webhook_url": self.webhook_url}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.webhook_url, json={"text": message})
                result = {"status": "ok", "message": "通知已发送"}
                latency = int((time.time() - start_time) * 1000)
                log_api_call(
                    provider="webhook_notify_provider",
                    endpoint=self.webhook_url,
                    request_data=request_data,
                    response_data=result,
                    success=True,
                    latency_ms=latency,
                )
                return result
        except Exception as e:
            logger.error(f"[WebhookNotifyProvider] 发送失败: {e}")
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="webhook_notify_provider",
                endpoint=self.webhook_url,
                request_data=request_data,
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            return {"status": "error", "message": str(e)}

    async def test_connection(self) -> Dict:
        if not self.webhook_url:
            return {"status": "mock", "message": "未配置 Webhook URL"}
        return {"status": "ok", "message": "Webhook URL 已配置"}

    def get_provider_name(self) -> str:
        return "webhook_notify_provider"
