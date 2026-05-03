"""
系统监控服务 - 收集系统运行状态、API 调用统计、服务健康检查
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlmodel import Session, select, func
from app.database import engine, get_session
from app.models import APILog, Hotel, StrategyReport, OTAOrder, WechatMessage
from app.services.ai_provider import AIProvider

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控服务"""

    @classmethod
    def get_system_stats(cls, hours: int = 24) -> Dict:
        """获取系统整体统计"""
        now = datetime.now()
        since = now - timedelta(hours=hours)

        try:
            with Session(engine) as session:
                total_api_calls = session.exec(
                    select(func.count(APILog.id)).where(APILog.created_at >= since)
                ).one()

                successful_calls = session.exec(
                    select(func.count(APILog.id)).where(
                        APILog.created_at >= since, APILog.success == True
                    )
                ).one()

                failed_calls = session.exec(
                    select(func.count(APILog.id)).where(
                        APILog.created_at >= since, APILog.success == False
                    )
                ).one()

                avg_latency = session.exec(
                    select(func.avg(APILog.latency_ms)).where(
                        APILog.created_at >= since, APILog.latency_ms.isnot(None)
                    )
                ).one()

                total_hotels = session.exec(select(func.count(Hotel.id))).one()
                total_strategies = session.exec(
                    select(func.count(StrategyReport.id)).where(StrategyReport.created_at >= since)
                ).one()
                total_orders = session.exec(
                    select(func.count(OTAOrder.id)).where(OTAOrder.created_at >= since)
                ).one()
                total_messages = session.exec(
                    select(func.count(WechatMessage.id)).where(WechatMessage.created_at >= since)
                ).one()

                return {
                    "period_hours": hours,
                    "api_calls": {
                        "total": total_api_calls or 0,
                        "successful": successful_calls or 0,
                        "failed": failed_calls or 0,
                        "success_rate": round(
                            (successful_calls / total_api_calls * 100) if total_api_calls > 0 else 0, 1
                        ),
                        "avg_latency_ms": round(avg_latency or 0, 1),
                    },
                    "business": {
                        "hotels": total_hotels or 0,
                        "strategies_generated": total_strategies or 0,
                        "orders": total_orders or 0,
                        "wechat_messages": total_messages or 0,
                    },
                }
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {"error": str(e)}

    @classmethod
    def get_provider_stats(cls, hours: int = 24) -> Dict:
        """获取各 Provider 的调用统计"""
        now = datetime.now()
        since = now - timedelta(hours=hours)

        try:
            with Session(engine) as session:
                provider_stats = {}
                logs = session.exec(
                    select(APILog).where(APILog.created_at >= since).order_by(APILog.created_at.desc())
                ).all()

                for log in logs:
                    if log.provider not in provider_stats:
                        provider_stats[log.provider] = {
                            "total": 0,
                            "successful": 0,
                            "failed": 0,
                            "total_latency": 0,
                            "latency_count": 0,
                            "last_error": None,
                        }

                    stats = provider_stats[log.provider]
                    stats["total"] += 1
                    if log.success:
                        stats["successful"] += 1
                    else:
                        stats["failed"] += 1
                        stats["last_error"] = log.error_message

                    if log.latency_ms:
                        stats["total_latency"] += log.latency_ms
                        stats["latency_count"] += 1

                for name, stats in provider_stats.items():
                    if stats["latency_count"] > 0:
                        stats["avg_latency_ms"] = round(
                            stats["total_latency"] / stats["latency_count"], 1
                        )
                    else:
                        stats["avg_latency_ms"] = 0
                    stats.pop("total_latency", None)
                    stats.pop("latency_count", None)

                return provider_stats
        except Exception as e:
            logger.error(f"获取 Provider 统计失败: {e}")
            return {}

    @classmethod
    async def health_check(cls) -> Dict:
        """系统健康检查"""
        results = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
        }

        try:
            with Session(engine) as session:
                hotels = session.exec(select(func.count(Hotel.id))).one()
                results["checks"]["database"] = {
                    "status": "healthy",
                    "message": f"数据库连接正常，{hotels or 0} 家酒店",
                }
        except Exception as e:
            results["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
            results["status"] = "degraded"

        try:
            ai = AIProvider()
            if ai.api_key:
                result = await ai.test_connection()
                results["checks"]["ai_api"] = {
                    "status": "healthy" if result.get("status") == "ok" else "warning",
                    "message": result.get("message", "未知"),
                }
            else:
                results["checks"]["ai_api"] = {
                    "status": "not_configured",
                    "message": "未配置 AI API Key，使用 Mock 模式",
                }
        except Exception as e:
            results["checks"]["ai_api"] = {"status": "unhealthy", "message": str(e)}

        try:
            from app.services.wechat.wechat_provider import get_wechat_provider
            wechat = get_wechat_provider()
            test = await wechat.test_connection()
            results["checks"]["wechat"] = {
                "status": "healthy" if test.get("status") == "ok" else "warning",
                "message": test.get("message", "未知"),
            }
        except Exception as e:
            results["checks"]["wechat"] = {"status": "unhealthy", "message": str(e)}

        if any(c["status"] in ["unhealthy"] for c in results["checks"].values()):
            results["status"] = "unhealthy"
        elif any(c["status"] in ["warning", "degraded"] for c in results["checks"].values()):
            results["status"] = "degraded"

        return results

    @classmethod
    def get_recent_errors(cls, limit: int = 20) -> List[Dict]:
        """获取最近的错误日志"""
        try:
            with Session(engine) as session:
                logs = session.exec(
                    select(APILog)
                    .where(APILog.success == False)
                    .order_by(APILog.created_at.desc())
                    .limit(limit)
                ).all()

                return [
                    {
                        "id": log.id,
                        "provider": log.provider,
                        "endpoint": log.endpoint,
                        "error": log.error_message,
                        "latency_ms": log.latency_ms,
                        "created_at": log.created_at.isoformat() if log.created_at else None,
                    }
                    for log in logs
                ]
        except Exception as e:
            logger.error(f"获取错误日志失败: {e}")
            return []

    @classmethod
    def get_api_logs_timeline(cls, hours: int = 24, limit: int = 50) -> List[Dict]:
        """获取 API 调用时间线"""
        now = datetime.now()
        since = now - timedelta(hours=hours)

        try:
            with Session(engine) as session:
                logs = session.exec(
                    select(APILog)
                    .where(APILog.created_at >= since)
                    .order_by(APILog.created_at.desc())
                    .limit(limit)
                ).all()

                return [
                    {
                        "id": log.id,
                        "provider": log.provider,
                        "endpoint": log.endpoint,
                        "success": log.success,
                        "latency_ms": log.latency_ms,
                        "error": log.error_message,
                        "created_at": log.created_at.isoformat() if log.created_at else None,
                    }
                    for log in logs
                ]
        except Exception as e:
            logger.error(f"获取 API 时间线失败: {e}")
            return []
