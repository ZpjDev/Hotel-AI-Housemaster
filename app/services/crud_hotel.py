from app.models import Hotel
from sqlmodel import Session, select
from typing import Optional, List


def create_hotel(session: Session, hotel: Hotel) -> Hotel:
    session.add(hotel)
    session.commit()
    session.refresh(hotel)
    return hotel


def get_hotel(session: Session, hotel_id: int) -> Optional[Hotel]:
    return session.get(Hotel, hotel_id)


def get_hotels(session: Session, skip: int = 0, limit: int = 100) -> List[Hotel]:
    statement = select(Hotel).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_hotel_by_openid(session: Session, openid: str) -> Optional[Hotel]:
    statement = select(Hotel).where(Hotel.boss_openid == openid)
    return session.exec(statement).first()


def update_hotel(session: Session, hotel_id: int, update_data: dict) -> Optional[Hotel]:
    hotel = session.get(Hotel, hotel_id)
    if not hotel:
        return None
    for key, value in update_data.items():
        if value is not None:
            setattr(hotel, key, value)
    from datetime import datetime
    hotel.updated_at = datetime.now()
    session.add(hotel)
    session.commit()
    session.refresh(hotel)
    return hotel


def delete_hotel(session: Session, hotel_id: int) -> bool:
    hotel = session.get(Hotel, hotel_id)
    if not hotel:
        return False
    session.delete(hotel)
    session.commit()
    return True
