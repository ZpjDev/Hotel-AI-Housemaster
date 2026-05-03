import logging
import time
from typing import List, Dict, Any
from datetime import datetime
from app.config import settings
from app.services.external_api.base_provider import OTADataProvider, CompetitorPriceData, ProviderResult
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)


class ThirdPartyOTAProvider(OTADataProvider):
    """合规第三方 OTA 数据 Provider

    数据来源必须是用户授权的第三方 API 或合作接口，不能是违规爬虫。
    支持真实外部 API 接入，自动降级到 Mock。

    ========================================================================
    真实 API 接入指南（按顺序修改以下标记处）
    ========================================================================

    ① 修改请求 endpoint（约第 104 行）
    ----------------------------------------
    当前: endpoint = f"{self.api_base}/competitor/prices"
    改为: endpoint = f"{self.api_base}/你的实际路径"
    例如: endpoint = f"{self.api_base}/v2/hotel/price/query"

    ② 修改请求 body（约第 105 行）
    ----------------------------------------
    当前: request_payload = {"competitor_id": competitor_id, "dates": dates}
    改为: 根据真实 API 要求的字段格式，例如：
          request_payload = {
              "hotelIds": [competitor_id],
              "startDate": dates[0],
              "endDate": dates[-1],
              "currency": "CNY"
          }

    ③ 修改认证 header（约第 117-121 行）
    ----------------------------------------
    当前: headers = {"Authorization": f"Bearer {self.api_key}", ...}
    改为: 根据真实 API 认证方式，例如：
          - API Key 放在 Header: {"X-API-Key": self.api_key, ...}
          - Basic Auth: 使用 base64 编码
          - OAuth2: {"Authorization": f"Bearer {access_token}", ...}
          - 需要额外 header: 在此 dict 中追加

    ④ 修改返回字段映射（_map_api_response 方法，约第 37-89 行）
    ----------------------------------------
    当前: 支持常见字段名自动映射（target_date/date, remaining_rooms/available_rooms 等）
    改为: 根据真实 API 返回结构调整映射逻辑，例如：
          if "hotelPriceInfo" in item:
              item = item["hotelPriceInfo"]
          date = item.get("stayDate")
          price = item["rates"]["baseRate"]["amount"]
          注意：只需修改 _map_api_response 内部逻辑，外部调用不变

    ⑤ 处理分页（如需，约第 130-142 行）
    ----------------------------------------
    当前: 假设单次请求返回全部数据
    改为: 如果 API 分页，例如：
          page = 1
          while True:
              response = await client.post(endpoint, ..., json={..., "page": page})
              items = response.json().get("items", [])
              results.extend(self._map_api_response(item, ...) for item in items)
              if len(items) < page_size: break
              page += 1

    ⑥ 处理频率限制（如需，约第 113-176 行 try 块内）
    ----------------------------------------
    当前: 无节流，直接发送请求
    改为: 如需限流，在请求前添加：
          import asyncio
          await asyncio.sleep(1.0)  # 每秒1次请求
          或使用令牌桶/滑动窗口算法
          如 API 返回 429，捕获后 retry with backoff
    ========================================================================
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

    def _mask_api_key(self) -> str:
        """安全的 API Key 掩码，用于日志"""
        if not self.api_key:
            return "(empty)"
        if len(self.api_key) <= 8:
            return "***" + self.api_key[-2:]
        return self.api_key[:3] + "***" + self.api_key[-4:]

    def _map_api_response(self, item: Dict[str, Any], competitor_id: int, competitor_name: str) -> CompetitorPriceData:
        """将真实 OTA API 响应映射为内部竞品价格数据

        内部字段必须包括：
        - competitor_id
        - platform
        - target_date (映射为 date)
        - room_type
        - price
        - remaining_rooms
        - availability_status
        - breakfast_included
        - cancellable
        - promotion_text
        - source_type
        - captured_at
        """
        date = item.get("target_date") or item.get("date") or ""
        price = float(item.get("price", 0))
        remaining = item.get("remaining_rooms", item.get("available_rooms", 0))
        avail_status = item.get("availability_status", "")
        is_bookable = avail_status in ("available", "bookable", "yes", "true", "1", "") if avail_status else item.get("is_bookable", True)
        breakfast = item.get("breakfast_included", False)
        cancellable = item.get("cancellable", None)
        cancellation_policy = "free_cancellation" if cancellable else (item.get("cancellation_policy", None))
        promotion_text = item.get("promotion_text", item.get("promotion_info", None))
        platform = item.get("platform", competitor_name)
        room_type = item.get("room_type", None)
        source_type = item.get("source_type", "ota_api")
        captured_at_raw = item.get("captured_at", None)
        captured_at = captured_at_raw
        if not captured_at:
            captured_at = datetime.utcnow().isoformat()

        return CompetitorPriceData(
            competitor_id=competitor_id,
            competitor_name=competitor_name,
            date=date,
            price=price,
            available_rooms=remaining if remaining is not None else 0,
            is_bookable=is_bookable if isinstance(is_bookable, bool) else True,
            breakfast_included=breakfast if isinstance(breakfast, bool) else False,
            cancellation_policy=cancellation_policy,
            promotion_info=promotion_text,
            platform=platform,
            room_type=room_type,
            remaining_rooms=remaining,
            availability_status=avail_status or ("available" if is_bookable else "sold_out"),
            cancellable=cancellable,
            promotion_text=promotion_text,
            source_type=source_type,
            captured_at=captured_at,
        )

    async def get_competitor_prices(
        self,
        competitor_id: int,
        competitor_name: str,
        dates: List[str],
    ) -> List[CompetitorPriceData]:
        if not self.api_base or not self.api_key:
            logger.warning("[ThirdPartyOTAProvider] 未配置 API，使用 Mock 降级")
            from app.services.external_api.mock_ota_provider import MockOTAProvider
            mock = MockOTAProvider()
            return await mock.get_competitor_prices(competitor_id, competitor_name, dates)

        start_time = time.time()
        endpoint = f"{self.api_base}/competitor/prices"
        request_payload = {"competitor_id": competitor_id, "dates": dates}
        
        safe_request_log = {
            "competitor_id": competitor_id,
            "dates_count": len(dates),
            "endpoint": endpoint,
        }

        try:
            import httpx
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=request_payload,
                )
                
                latency = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    raw_items = data.get("prices", data.get("data", data.get("items", [])))
                    if isinstance(raw_items, list):
                        for item in raw_items:
                            try:
                                mapped = self._map_api_response(item, competitor_id, competitor_name)
                                results.append(mapped)
                            except Exception as map_err:
                                logger.warning(f"映射单条 OTA 数据失败: {map_err}, item={item}")
                                continue
                    
                    log_api_call(
                        provider="third_party_ota_provider",
                        endpoint=endpoint,
                        request_data=safe_request_log,
                        response_data={"count": len(results), "status": "success"},
                        success=True,
                        latency_ms=latency,
                    )
                    return results
                else:
                    log_api_call(
                        provider="third_party_ota_provider",
                        endpoint=endpoint,
                        request_data=safe_request_log,
                        response_data={"status_code": response.status_code, "detail": response.text[:200]},
                        success=False,
                        error_message=f"API returned {response.status_code}",
                        latency_ms=latency,
                    )
                    return await self._fallback(competitor_id, competitor_name, dates)

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            log_api_call(
                provider="third_party_ota_provider",
                endpoint=endpoint,
                request_data=safe_request_log,
                response_data=None,
                success=False,
                error_message=str(e),
                latency_ms=latency,
            )
            return await self._fallback(competitor_id, competitor_name, dates)

    async def _fallback(self, competitor_id: int, competitor_name: str, dates: List[str]) -> List[CompetitorPriceData]:
        """真实 API 失败时的降级策略"""
        try:
            from app.services.external_api.mock_ota_provider import MockOTAProvider
            mock = MockOTAProvider()
            return await mock.get_competitor_prices(competitor_id, competitor_name, dates)
        except Exception:
            logger.error("[ThirdPartyOTAProvider] Mock 降级也失败，返回空列表")
            return []

    async def test_connection(self) -> dict:
        if not self.api_base or not self.api_key:
            return {"status": "mock", "message": "未配置第三方 API，使用 Mock 模式"}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.api_base}/health",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return {"status": "ok", "message": f"第三方 OTA API 连接成功: {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"第三方 OTA API 连接失败: {e}"}

    def get_provider_name(self) -> str:
        return "third_party_ota_provider"
