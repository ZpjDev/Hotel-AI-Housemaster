from fastapi import APIRouter
from app.services.system_monitor import SystemMonitor

router = APIRouter()


@router.get("/monitor/stats")
async def api_system_stats(hours: int = 24):
    stats = SystemMonitor.get_system_stats(hours=hours)
    return stats


@router.get("/monitor/providers")
async def api_provider_stats(hours: int = 24):
    stats = SystemMonitor.get_provider_stats(hours=hours)
    return stats


@router.get("/monitor/health")
async def api_health_check():
    health = await SystemMonitor.health_check()
    return health


@router.get("/monitor/errors")
async def api_recent_errors(limit: int = 20):
    errors = SystemMonitor.get_recent_errors(limit=limit)
    return errors


@router.get("/monitor/timeline")
async def api_timeline(hours: int = 24, limit: int = 50):
    timeline = SystemMonitor.get_api_logs_timeline(hours=hours, limit=limit)
    return timeline
