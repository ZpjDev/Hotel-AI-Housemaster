import random
import logging
from typing import List
from app.utils.api_log import log_api_call
from app.services.external_api.base_provider import OTADataProvider, CompetitorPriceData

logger = logging.getLogger(__name__)


class MockOTAProvider(OTADataProvider):
    """Mock OTA Provider - 用于开发和测试"""

    def __init__(self):
        self.base_prices = {
            "经济型酒店": [150, 250],
            "中端酒店": [250, 450],
            "高端酒店": [450, 800],
            "豪华酒店": [800, 1500],
        }

    async def get_competitor_prices(
        self,
        competitor_id: int,
        competitor_name: str,
        dates: List[str],
    ) -> List[CompetitorPriceData]:
        import time
        start = time.time()
        try:
            results = []
            hotel_type = random.choice(list(self.base_prices.keys()))
            min_price, max_price = self.base_prices[hotel_type]

            for date in dates:
                base_price = random.randint(min_price, max_price)
                available_rooms = random.randint(0, 50)
                price_data = CompetitorPriceData(
                    competitor_id=competitor_id,
                    competitor_name=competitor_name,
                    date=date,
                    price=round(base_price + random.uniform(-20, 50), 0),
                    available_rooms=available_rooms,
                    is_bookable=available_rooms > 0,
                    breakfast_included=random.choice([True, False]),
                    cancellation_policy=random.choice(["免费取消", "不可取消", "限时取消"]),
                    promotion_info=random.choice(["", "连住优惠", "早鸟价", "限时折扣", ""]),
                )
                results.append(price_data)

            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_ota_provider", "/competitor/prices",
                request_data=f'{{"competitor_id":{competitor_id},"dates":{dates}}}',
                response_data=f'{{"count":{len(results)}}}',
                success=True, latency_ms=round(latency, 2),
            )
            return results
        except Exception as e:
            latency = (time.time() - start) * 1000
            log_api_call(
                "mock_ota_provider", "/competitor/prices",
                request_data=f'{{"competitor_id":{competitor_id}}}',
                success=False, error_message=str(e), latency_ms=round(latency, 2),
            )
            raise

    async def test_connection(self) -> dict:
        return {"status": "ok", "message": "Mock OTA Provider 连接成功"}

    def get_provider_name(self) -> str:
        return "mock_ota_provider"
