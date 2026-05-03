import logging
from datetime import datetime
from sqlmodel import Session
from app.database import engine
from app.services.external_api.ota_data_service import OTADataService
from app.services.ai_provider import AIProvider
from app.services.strategy_service import StrategyService
from app.services.wechat.wechat_provider import get_wechat_provider
from app.models import StrategyReport
from app.services.crud_strategy import create_strategy_report

logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度服务 - 修复版：每个任务新建 session"""

    def __init__(self):
        self.scheduler = None

    def init_scheduler(self):
        """初始化定时任务调度器"""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        self.scheduler = AsyncIOScheduler()

        schedule_times = [
            ("09:00", "morning"),
            ("12:00", "noon"),
            ("16:00", "afternoon"),
            ("18:00", "evening"),
            ("22:00", "night"),
        ]

        for time_str, slot in schedule_times:
            hour, minute = map(int, time_str.split(":"))
            self.scheduler.add_job(
                self._run_strategy_task,
                "cron",
                hour=hour,
                minute=minute,
                id=f"{slot}_strategy",
                args=[slot],
                misfire_grace_time=3600,
            )

    async def _run_strategy_task(self, time_slot: str):
        """执行定时策略任务"""
        from app.services.crud_hotel import get_hotels

        logger.info(f"开始执行 {time_slot} 定时策略任务")

        with Session(engine) as session:
            hotels = get_hotels(session)
            logger.info(f"找到 {len(hotels)} 个酒店")

            for hotel in hotels:
                try:
                    await self._process_hotel(session, hotel, time_slot)
                except Exception as e:
                    logger.error(f"酒店 {hotel.name} {time_slot} 策略任务失败: {e}")
                    continue

    async def _process_hotel(self, session, hotel, time_slot: str):
        """处理单个酒店的定时任务"""
        today = datetime.now().strftime("%Y-%m-%d")
        is_fallback = False

        try:
            ota = OTADataService(session)
            await ota.sync_competitor_prices(hotel.id, days=[0, 1, 2, 3, 5, 7, 15, 30])
        except Exception as e:
            logger.warning(f"同步竞品价格失败，使用已有数据: {e}")
            is_fallback = True

        try:
            ai = AIProvider()
            ota = OTADataService(session)
            strategy_svc = StrategyService(session, ai, ota)

            strategy = await strategy_svc.generate_strategy(
                hotel_id=hotel.id,
                target_date=today,
                time_slot=time_slot,
                question=None,
            )

            fallback_note = "（数据未更新，使用已有数据）" if is_fallback else ""
            strategy["full_report"] += f"\n\n---\n报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{fallback_note}"

            import json
            sp_json = json.dumps(strategy.get("suggested_prices", []), ensure_ascii=False)
            ar_json = json.dumps(strategy.get("actions_required", []), ensure_ascii=False)

            report = StrategyReport(
                hotel_id=hotel.id,
                date=today,
                time_slot=time_slot,
                market_analysis=strategy.get("market_analysis", ""),
                competitor_analysis=strategy.get("competitor_analysis", ""),
                suggested_price=strategy.get("suggested_price", ""),
                suggested_prices_json=sp_json,
                room_control_strategy=strategy.get("room_control_strategy", ""),
                ota_strategy=strategy.get("ota_strategy", ""),
                promotion_strategy=strategy.get("promotion_strategy", ""),
                direct_customer_strategy=strategy.get("direct_customer_strategy", ""),
                risk_alert=strategy.get("risk_alert", ""),
                actions_required_json=ar_json,
                full_report=strategy.get("full_report", ""),
                created_at=datetime.now(),
            )
            create_strategy_report(session, report)

            await self._send_notification(hotel.boss_openid, strategy.get("suggested_price", ""))
            logger.info(f"酒店 {hotel.name} {time_slot} 策略任务完成")
        except Exception as e:
            logger.error(f"生成策略报告失败: {e}")

    async def _send_notification(self, openid: str, message: str):
        """发送微信通知"""
        try:
            provider = get_wechat_provider()
            await provider.send_message(openid, f"【经营策略提醒】\n{message}")
        except Exception as e:
            logger.error(f"发送通知失败: {e}")

    def start(self):
        """启动调度器"""
        if self.scheduler:
            self.scheduler.start()
            logger.info("定时任务调度器已启动")

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("定时任务调度器已关闭")
