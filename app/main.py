from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import create_db_and_tables
from app.routers import business, ai, management, admin, external, wechat, api_logs, monitor
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    create_db_and_tables()

    from app.services.scheduler_service import SchedulerService
    from app.config import settings

    if settings.SCHEDULER_ENABLED:
        scheduler_svc = SchedulerService()
        scheduler_svc.init_scheduler()
        scheduler_svc.start()
        app.state.scheduler = scheduler_svc

    yield

    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    description="酒店/民宿 AI 智能管家系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(business.router, prefix="/api", tags=["业务管理"])
app.include_router(ai.router, prefix="/api", tags=["AI 策略"])
app.include_router(management.router, prefix="/api", tags=["运营管理"])
app.include_router(external.router, prefix="/api", tags=["外部同步"])
app.include_router(api_logs.router, prefix="/api", tags=["API 调用日志"])
app.include_router(wechat.router, prefix="/wechat", tags=["微信"])
app.include_router(admin.router, tags=["后台管理"])
app.include_router(monitor.router, tags=["系统监控"])


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "admin": "/admin",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
