import json
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CompetitorPriceData(BaseModel):
    competitor_id: int
    competitor_name: str
    date: str
    price: float
    available_rooms: int
    is_bookable: bool
    breakfast_included: bool = False
    cancellation_policy: Optional[str] = None
    promotion_info: Optional[str] = None
    platform: Optional[str] = None
    room_type: Optional[str] = None
    remaining_rooms: Optional[int] = None
    availability_status: Optional[str] = None
    cancellable: Optional[bool] = None
    promotion_text: Optional[str] = None
    source_type: Optional[str] = None
    captured_at: Optional[str] = None


class ProviderResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    provider: str = ""
    latency_ms: float = 0.0


class OTADataProvider(ABC):
    """统一 OTA 数据 Provider 抽象基类"""

    @abstractmethod
    async def get_competitor_prices(
        self,
        competitor_id: int,
        competitor_name: str,
        dates: List[str],
    ) -> List[CompetitorPriceData]:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    async def call_with_logging(self, coro, endpoint: str, request_data: str = "") -> ProviderResult:
        """统一调用包装：使用 app.utils.api_log.log_api_call 记录日志"""
        from app.utils.api_log import log_api_call
        start = time.time()
        try:
            result = await coro
            latency = (time.time() - start) * 1000
            log_api_call(
                provider=self.get_provider_name(),
                endpoint=endpoint,
                request_data=request_data,
                response_data=json.dumps(result, ensure_ascii=False)[:500],
                success=True,
                latency_ms=round(latency, 2),
            )
            return ProviderResult(
                success=True,
                data=result,
                provider=self.get_provider_name(),
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                provider=self.get_provider_name(),
                endpoint=endpoint,
                request_data=request_data,
                success=False,
                error_message=str(e),
                latency_ms=round(latency, 2),
            )
            logger.error(f"[{self.get_provider_name()}] {endpoint} 失败: {e}")
            return ProviderResult(
                success=False,
                error=str(e),
                provider=self.get_provider_name(),
                latency_ms=round(latency, 2),
            )


class WechatProvider(ABC):
    """微信 Provider 抽象基类"""

    @abstractmethod
    async def send_message(self, openid: str, message: str) -> Dict:
        pass

    @abstractmethod
    async def parse_message(self, payload: Dict) -> Dict:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class PhoneProvider(ABC):
    """电话 Provider 抽象基类"""

    @abstractmethod
    async def handle_inbound_call(self, payload: Dict) -> Dict:
        pass

    @abstractmethod
    async def transcribe_call(self, audio_url: str) -> str:
        pass

    @abstractmethod
    async def answer_question(self, call_text: str, hotel_id: int) -> str:
        pass

    @abstractmethod
    async def transfer_to_human(self, reason: str) -> Dict:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class MapProvider(ABC):
    """地图 Provider 抽象基类"""

    @abstractmethod
    async def get_distance(self, origin: str, destination: str) -> Dict:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class NotifyProvider(ABC):
    """通知 Provider 抽象基类"""

    @abstractmethod
    async def send_notification(self, target: str, message: str, channel: str = "webhook") -> Dict:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class OrderProvider(ABC):
    """订单 Provider 抽象基类"""

    @abstractmethod
    async def get_orders(self, hotel_id: int, date: str) -> List[Dict]:
        pass

    @abstractmethod
    async def confirm_order(self, order_no: str) -> Dict:
        pass

    @abstractmethod
    async def cancel_order(self, order_no: str) -> Dict:
        pass

    @abstractmethod
    async def modify_order(self, order_no: str, changes: Dict) -> Dict:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass
