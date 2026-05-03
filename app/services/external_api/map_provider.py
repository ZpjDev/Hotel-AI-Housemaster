import logging
import time
from typing import Dict
from app.services.external_api.base_provider import MapProvider
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class MockMapProvider(MapProvider):
    """Mock 地图 Provider"""

    async def get_distance(self, origin: str, destination: str) -> Dict:
        start_time = time.time()
        import random
        try:
            logger.info(f"[MockMapProvider] 计算 {origin} 到 {destination} 距离")
            result = {
                "origin": origin,
                "destination": destination,
                "distance_km": round(random.uniform(0.5, 10), 1),
                "duration_min": random.randint(5, 30),
            }
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="mock_map_provider",
                endpoint="get_distance",
                request_data={"origin": origin, "destination": destination},
                response_data=result,
                success=True,
                latency_ms=latency,
            )
            return result
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="mock_map_provider",
                endpoint="get_distance",
                request_data={"origin": origin, "destination": destination},
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            raise

    async def test_connection(self) -> Dict:
        return {"status": "ok", "message": "Mock Map Provider 可用"}

    def get_provider_name(self) -> str:
        return "mock_map_provider"
