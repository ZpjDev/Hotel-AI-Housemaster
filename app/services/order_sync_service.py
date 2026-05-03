"""
订单同步服务 - 模块化 OTA 订单自动同步
支持 PMS 对接、OTA API 对接、手动录入多种模式
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlmodel import Session, select

from app.models import OTAOrder, Hotel, WechatMessage
from app.services.external_api.order_provider import MockOrderProvider
from app.services.external_api.base_provider import OrderProvider
from app.services.crud_strategy import create_wechat_message

logger = logging.getLogger(__name__)


class OrderSyncService:
    """订单同步服务"""

    def __init__(self, db: Session, provider: OrderProvider = None):
        self.db = db
        self.provider = provider or MockOrderProvider()

    async def sync_today_orders(self, hotel_id: int, date: str = None) -> Dict:
        """同步今日订单"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        try:
            remote_orders = await self.provider.get_orders(hotel_id, date)
            synced = 0
            updated = 0
            cancelled = 0

            for order_data in remote_orders:
                order_no = order_data.get("order_no", "")
                if not order_no:
                    continue

                existing = self.db.exec(
                    select(OTAOrder).where(OTAOrder.order_no == order_no)
                ).first()

                if existing:
                    existing.amount = order_data.get("amount", existing.amount)
                    existing.status = order_data.get("status", existing.status)
                    existing.updated_at = datetime.now()
                    if existing.status == "cancelled":
                        cancelled += 1
                    else:
                        updated += 1
                    self.db.add(existing)
                else:
                    new_order = OTAOrder(
                        hotel_id=hotel_id,
                        platform=order_data.get("platform", "unknown"),
                        order_no=order_no,
                        customer_name=order_data.get("customer_name", ""),
                        customer_phone=order_data.get("customer_phone", ""),
                        room_type=order_data.get("room_type", ""),
                        check_in_date=order_data.get("check_in_date", date),
                        check_out_date=order_data.get("check_out_date", date),
                        amount=order_data.get("amount", 0.0),
                        status=order_data.get("status", "pending"),
                    )
                    self.db.add(new_order)
                    synced += 1

            self.db.commit()
            return {
                "success": True,
                "synced": synced,
                "updated": updated,
                "cancelled": cancelled,
                "message": f"同步完成：新增 {synced} 单，更新 {updated} 单，取消 {cancelled} 单",
            }
        except Exception as e:
            logger.error(f"订单同步失败: {e}")
            return {"success": False, "message": f"同步失败: {str(e)}"}

    async def sync_orders_by_period(self, hotel_id: int, start_date: str, end_date: str) -> Dict:
        """同步一段时间内的订单"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        total_synced = 0
        total_updated = 0
        total_cancelled = 0

        current = start
        while current <= end:
            result = await self.sync_today_orders(hotel_id, current.strftime("%Y-%m-%d"))
            total_synced += result.get("synced", 0)
            total_updated += result.get("updated", 0)
            total_cancelled += result.get("cancelled", 0)
            current += timedelta(days=1)

        return {
            "success": True,
            "synced": total_synced,
            "updated": total_updated,
            "cancelled": total_cancelled,
            "period": f"{start_date} ~ {end_date}",
            "message": f"同步完成：新增 {total_synced} 单，更新 {total_updated} 单，取消 {total_cancelled} 单",
        }

    async def notify_new_orders(self, hotel_id: int, synced: int):
        """通知酒店有新订单"""
        hotel = self.db.get(Hotel, hotel_id)
        if not hotel or not hotel.boss_openid:
            return

        wechat_msg = WechatMessage(
            hotel_id=hotel_id,
            openid=hotel.boss_openid,
            message="系统自动通知",
            intent="system",
            response=f"您有 {synced} 个新订单，请及时处理。",
            created_at=datetime.now(),
        )
        create_wechat_message(self.db, wechat_msg)
