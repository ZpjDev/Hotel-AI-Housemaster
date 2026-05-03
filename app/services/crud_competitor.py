from app.models import CompetitorHotel, CompetitorPrice
from sqlmodel import Session, select
from typing import Optional, List


def create_competitor(session: Session, competitor: CompetitorHotel) -> CompetitorHotel:
    session.add(competitor)
    session.commit()
    session.refresh(competitor)
    return competitor


def get_competitors(session: Session, hotel_id: int) -> List[CompetitorHotel]:
    statement = select(CompetitorHotel).where(CompetitorHotel.hotel_id == hotel_id)
    return list(session.exec(statement).all())


def get_competitor(session: Session, competitor_id: int) -> Optional[CompetitorHotel]:
    return session.get(CompetitorHotel, competitor_id)


def create_competitor_price(session: Session, price: CompetitorPrice) -> CompetitorPrice:
    session.add(price)
    session.commit()
    session.refresh(price)
    return price


def get_competitor_prices(
    session: Session, competitor_id: int, start_date: str = None, end_date: str = None
) -> List[CompetitorPrice]:
    statement = select(CompetitorPrice).where(CompetitorPrice.competitor_id == competitor_id)
    if start_date:
        statement = statement.where(CompetitorPrice.date >= start_date)
    if end_date:
        statement = statement.where(CompetitorPrice.date <= end_date)
    statement = statement.order_by(CompetitorPrice.date)
    return list(session.exec(statement).all())


def get_latest_competitor_price(session: Session, competitor_id: int, date: str) -> Optional[CompetitorPrice]:
    statement = select(CompetitorPrice).where(
        CompetitorPrice.competitor_id == competitor_id,
        CompetitorPrice.date == date
    )
    return session.exec(statement).first()
