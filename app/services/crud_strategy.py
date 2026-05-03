from app.models import StrategyReport
from sqlmodel import Session
from typing import Optional, List


def create_strategy_report(session: Session, report: StrategyReport) -> StrategyReport:
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def get_strategy_report(session: Session, report_id: int) -> Optional[StrategyReport]:
    return session.get(StrategyReport, report_id)


def get_strategy_reports(
    session: Session, hotel_id: int, date: str = None
) -> List[StrategyReport]:
    from sqlmodel import select
    statement = select(StrategyReport).where(StrategyReport.hotel_id == hotel_id)
    if date:
        statement = statement.where(StrategyReport.date == date)
    statement = statement.order_by(StrategyReport.created_at.desc())
    return list(session.exec(statement).all())


def create_wechat_message(session: Session, message) -> object:
    from app.models import WechatMessage
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def get_wechat_messages(session: Session, hotel_id: int, limit: int = 20) -> list:
    from sqlmodel import select
    from app.models import WechatMessage
    statement = select(WechatMessage).where(WechatMessage.hotel_id == hotel_id).order_by(WechatMessage.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())
