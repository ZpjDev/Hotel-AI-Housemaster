import logging
import json
from sqlmodel import Session
from datetime import datetime
from app.models import APILog
from app.database import engine

logger = logging.getLogger(__name__)


def log_api_call(
    provider: str,
    endpoint: str,
    request_data=None,
    response_data=None,
    success: bool = True,
    error_message: str = None,
    latency_ms: float = None,
):
    """统一记录 API 调用日志（无需传入 session，使用 Session(engine)）"""
    try:
        if isinstance(request_data, (dict, list)):
            request_data = json.dumps(request_data, ensure_ascii=False, default=str)
        if isinstance(response_data, (dict, list)):
            response_data = json.dumps(response_data, ensure_ascii=False, default=str)

        log_entry = APILog(
            provider=provider,
            endpoint=endpoint,
            request_data=request_data,
            response_data=response_data,
            success=success,
            error_message=error_message,
            latency_ms=latency_ms,
            created_at=datetime.now(),
        )
        with Session(engine) as session:
            session.add(log_entry)
            session.commit()
    except Exception as e:
        logger.error(f"记录 API 日志失败: {e}")
