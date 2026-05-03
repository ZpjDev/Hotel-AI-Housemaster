import logging
import time
from typing import List, Dict
from app.services.external_api.base_provider import OTADataProvider, CompetitorPriceData
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class ManualOTAProvider(OTADataProvider):
    """手动录入 OTA Provider - 由用户手动输入竞品价格"""

    def __init__(self, manual_data: Dict[str, List[Dict]] = None):
        self.manual_data = manual_data or {}

    async def get_competitor_prices(
        self,
        competitor_id: int,
        competitor_name: str,
        dates: List[str],
    ) -> List[CompetitorPriceData]:
        start_time = time.time()
        request_data = {"competitor_id": competitor_id, "competitor_name": competitor_name, "dates": dates}
        try:
            results = []
            key = str(competitor_id)

            for date in dates:
                manual_entry = self.manual_data.get(key, {}).get(date)
                if manual_entry:
                    results.append(CompetitorPriceData(
                        competitor_id=competitor_id,
                        competitor_name=competitor_name,
                        date=date,
                        price=manual_entry.get("price", 0),
                        available_rooms=manual_entry.get("available_rooms", 0),
                        is_bookable=manual_entry.get("is_bookable", False),
                        breakfast_included=manual_entry.get("breakfast_included", False),
                        cancellation_policy=manual_entry.get("cancellation_policy"),
                        promotion_info=manual_entry.get("promotion_info"),
                    ))
                else:
                    logger.warning(f"[ManualProvider] 竞品 {competitor_name} {date} 无手动数据")

            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="manual_ota_provider",
                endpoint="manual_data_lookup",
                request_data=request_data,
                response_data={"count": len(results)},
                success=True,
                latency_ms=latency,
            )
            return results
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="manual_ota_provider",
                endpoint="manual_data_lookup",
                request_data=request_data,
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            raise

    def set_manual_data(self, competitor_id: int, date: str, data: Dict):
        key = str(competitor_id)
        if key not in self.manual_data:
            self.manual_data[key] = {}
        self.manual_data[key][date] = data

    async def test_connection(self) -> dict:
        return {"status": "ok", "message": "Manual OTA Provider 可用"}

    def get_provider_name(self) -> str:
        return "manual_ota_provider"
