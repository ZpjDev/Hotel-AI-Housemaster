from app.models import DailyBusiness
from sqlmodel import Session, select
from typing import Optional, List
from datetime import datetime


def create_daily_business(session: Session, business: DailyBusiness) -> DailyBusiness:
    if business.available_rooms is None:
        business.available_rooms = business.total_rooms - business.sold_rooms

    if business.sold_rooms > 0:
        business.occupancy_rate = round(business.sold_rooms / business.total_rooms * 100, 2)
    else:
        business.occupancy_rate = 0.0

    if business.sold_rooms > 0:
        business.adr = round(business.total_revenue / business.sold_rooms, 2)
    else:
        business.adr = 0.0

    business.revpar = round(business.adr * business.occupancy_rate / 100, 2)

    session.add(business)
    session.commit()
    session.refresh(business)
    return business


def get_daily_business(session: Session, hotel_id: int, date: str) -> Optional[DailyBusiness]:
    statement = select(DailyBusiness).where(
        DailyBusiness.hotel_id == hotel_id,
        DailyBusiness.date == date
    )
    return session.exec(statement).first()


def get_daily_business_range(
    session: Session, hotel_id: int, start_date: str, end_date: str
) -> List[DailyBusiness]:
    statement = select(DailyBusiness).where(
        DailyBusiness.hotel_id == hotel_id,
        DailyBusiness.date >= start_date,
        DailyBusiness.date <= end_date
    ).order_by(DailyBusiness.date)
    return list(session.exec(statement).all())


def get_monthly_business(session: Session, hotel_id: int, month: str) -> List[DailyBusiness]:
    statement = select(DailyBusiness).where(
        DailyBusiness.hotel_id == hotel_id,
        DailyBusiness.date.startswith(month)
    ).order_by(DailyBusiness.date)
    return list(session.exec(statement).all())
