from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List, Optional
from app.database import get_session
from app.models import APILog
from sqlmodel import select
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class APILogResponse(BaseModel):
    id: int
    provider: str
    endpoint: str
    request_data: Optional[str] = None
    response_data: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    latency_ms: Optional[float] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


router = APIRouter()


@router.get("/api-logs", response_model=List[APILogResponse])
def api_get_api_logs(
    provider: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = 50,
    session: Session = Depends(get_session),
):
    """查询 API 调用日志"""
    statement = select(APILog)
    if provider:
        statement = statement.where(APILog.provider == provider)
    if success is not None:
        statement = statement.where(APILog.success == success)
    statement = statement.order_by(APILog.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())
