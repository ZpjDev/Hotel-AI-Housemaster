from app.models import RoomType
from sqlmodel import Session, select
from typing import Optional, List


def create_room_type(session: Session, room_type: RoomType) -> RoomType:
    session.add(room_type)
    session.commit()
    session.refresh(room_type)
    return room_type


def get_room_type(session: Session, room_type_id: int) -> Optional[RoomType]:
    return session.get(RoomType, room_type_id)


def get_room_types(session: Session, hotel_id: int) -> List[RoomType]:
    statement = select(RoomType).where(RoomType.hotel_id == hotel_id)
    return list(session.exec(statement).all())


def update_room_type(session: Session, room_type_id: int, update_data: dict) -> Optional[RoomType]:
    room_type = session.get(RoomType, room_type_id)
    if not room_type:
        return None
    for key, value in update_data.items():
        if value is not None:
            setattr(room_type, key, value)
    from datetime import datetime
    room_type.updated_at = datetime.now()
    session.add(room_type)
    session.commit()
    session.refresh(room_type)
    return room_type
