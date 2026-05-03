import logging
import time
from typing import List
from app.config import settings
from app.services.external_api.base_provider import OTADataProvider, CompetitorPriceData
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class OfficialOTAProvider(OTADataProvider):
    """官方 OTA API Provider

    通过美团/携程/飞猪等平台的官方开放平台 API 获取数据。
    需要酒店/民宿老板授权后才能访问。
    """

    def __init__(self, api_base: str = None, api_key: str = None):
        from app.services.ai_provider import get_ota_config
        ota_cfg = get_ota_config()
        raw_key = api_key or ota_cfg["api_key"] or settings.OTA_API_KEY
        if not raw_key or raw_key.startswith("your-") or raw_key in ["your_api_key"]:
            self.api_key = ""
        else:
            self.api_key = raw_key
        self.api_base = api_base or ota_cfg["api_base"] or settings.OTA_API_BASE

    async def get_competitor_prices(
        self,
        competitor_id: int,
        competitor_name: str,
        dates: List[str],
    ) -> List[CompetitorPriceData]:
        if not self.api_base or not self.api_key:
            logger.warning("[OfficialOTAProvider] 未配置官方 API，使用 Mock 降级")
            from app.services.external_api.mock_ota_provider import MockOTAProvider
            mock = MockOTAProvider()
            return await mock.get_competitor_prices(competitor_id, competitor_name, dates)

        start_time = time.time()
        request_data = {"competitor_id": competitor_id, "competitor_name": competitor_name, "dates": dates}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.api_base}/v1/competitorPrices",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"competitor_id": competitor_id, "dates": ",".join(dates)},
                )
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get("data", []):
                        results.append(CompetitorPriceData(
                            competitor_id=competitor_id,
                            competitor_name=competitor_name,
                            date=item["date"],
                            price=item["price"],
                            available_rooms=item.get("available_rooms", 0),
                            is_bookable=item.get("is_bookable", True),
                        ))
                    latency = int((time.time() - start_time) * 1000)
                    log_api_call(
                        provider="official_ota_provider",
                        endpoint=f"{self.api_base}/v1/competitorPrices",
                        request_data=request_data,
                        response_data={"count": len(results)},
                        success=True,
                        latency_ms=latency,
                    )
                    return results
                else:
                    latency = int((time.time() - start_time) * 1000)
                    log_api_call(
                        provider="official_ota_provider",
                        endpoint=f"{self.api_base}/v1/competitorPrices",
                        request_data=request_data,
                        response_data={"status_code": response.status_code},
                        success=False,
                        error_message=f"API returned {response.status_code}",
                        latency_ms=latency,
                    )
                    from app.services.external_api.mock_ota_provider import MockOTAProvider
                    mock = MockOTAProvider()
                    return await mock.get_competitor_prices(competitor_id, competitor_name, dates)
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="official_ota_provider",
                endpoint=f"{self.api_base}/v1/competitorPrices",
                request_data=request_data,
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            from app.services.external_api.mock_ota_provider import MockOTAProvider
            mock = MockOTAProvider()
            return await mock.get_competitor_prices(competitor_id, competitor_name, dates)

    async def test_connection(self) -> dict:
        if not self.api_base or not self.api_key:
            return {"status": "mock", "message": "未配置官方 API，使用 Mock 模式"}
        return {"status": "ok", "message": "官方 OTA API 已配置"}

    def get_provider_name(self) -> str:
        return "official_ota_provider"
