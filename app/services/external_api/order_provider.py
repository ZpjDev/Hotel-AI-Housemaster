import logging
from typing import List, Dict
from app.services.external_api.base_provider import OrderProvider

logger = logging.getLogger(__name__)


class MockOrderProvider(OrderProvider):
    """Mock 订单 Provider - Phase 1 本地订单表"""

    async def get_orders(self, hotel_id: int, date: str) -> List[Dict]:
        logger.info(f"[MockOrderProvider] 查询酒店 {hotel_id} {date} 订单")
        return []

    async def confirm_order(self, order_no: str) -> Dict:
        logger.info(f"[MockOrderProvider] 确认订单 {order_no}")
        return {"status": "pending_approval", "message": "订单确认需老板确认后执行"}

    async def cancel_order(self, order_no: str) -> Dict:
        logger.info(f"[MockOrderProvider] 取消订单 {order_no}")
        return {"status": "pending_approval", "message": "订单取消需老板确认后执行"}

    async def modify_order(self, order_no: str, changes: Dict) -> Dict:
        logger.info(f"[MockOrderProvider] 修改订单 {order_no}")
        return {"status": "pending_approval", "message": "订单修改需老板确认后执行"}

    async def test_connection(self) -> Dict:
        return {"status": "ok", "message": "Mock Order Provider 可用"}

    def get_provider_name(self) -> str:
        return "mock_order_provider"
