from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.database import get_session
from app.models import Hotel, RoomType, DailyBusiness, CompetitorHotel, CompetitorPrice
from app.schemas import (
    HotelCreate, HotelUpdate, HotelResponse,
    RoomTypeCreate, RoomTypeUpdate, RoomTypeResponse,
    DailyBusinessCreate, DailyBusinessResponse,
    CompetitorHotelCreate, CompetitorHotelResponse,
    CompetitorPriceCreate, CompetitorPriceResponse,
)
from app.services.crud_hotel import create_hotel, get_hotel, get_hotels, update_hotel
from app.services.crud_room_type import create_room_type, get_room_type, get_room_types, update_room_type
from app.services.crud_business import create_daily_business
from app.services.crud_competitor import create_competitor, get_competitors, create_competitor_price, get_competitor_prices


router = APIRouter()


# ============ 酒店 ============
@router.post("/hotels", response_model=HotelResponse)
def api_create_hotel(data: HotelCreate, session: Session = Depends(get_session)):
    hotel = Hotel(**data.model_dump())
    return create_hotel(session, hotel)


@router.get("/hotels", response_model=List[HotelResponse])
def api_get_hotels(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    return get_hotels(session, skip, limit)


@router.get("/hotels/{hotel_id}", response_model=HotelResponse)
def api_get_hotel(hotel_id: int, session: Session = Depends(get_session)):
    hotel = get_hotel(session, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="酒店不存在")
    return hotel


@router.put("/hotels/{hotel_id}", response_model=HotelResponse)
def api_update_hotel(hotel_id: int, data: HotelUpdate, session: Session = Depends(get_session)):
    hotel = update_hotel(session, hotel_id, data.model_dump(exclude_unset=True))
    if not hotel:
        raise HTTPException(status_code=404, detail="酒店不存在")
    return hotel


# ============ 房型 ============
@router.post("/room-types", response_model=RoomTypeResponse)
def api_create_room_type(data: RoomTypeCreate, session: Session = Depends(get_session)):
    room_type = RoomType(**data.model_dump())
    return create_room_type(session, room_type)


@router.get("/hotels/{hotel_id}/room-types", response_model=List[RoomTypeResponse])
def api_get_room_types(hotel_id: int, session: Session = Depends(get_session)):
    return get_room_types(session, hotel_id)


@router.put("/room-types/{room_type_id}", response_model=RoomTypeResponse)
def api_update_room_type(
    room_type_id: int, data: RoomTypeUpdate, session: Session = Depends(get_session)
):
    room_type = update_room_type(session, room_type_id, data.model_dump(exclude_unset=True))
    if not room_type:
        raise HTTPException(status_code=404, detail="房型不存在")
    return room_type


# ============ 经营数据 ============
@router.post("/daily-business", response_model=DailyBusinessResponse)
def api_create_daily_business(data: DailyBusinessCreate, session: Session = Depends(get_session)):
    business = DailyBusiness(**data.model_dump())
    return create_daily_business(session, business)


@router.get("/hotels/{hotel_id}/daily-business", response_model=List[DailyBusinessResponse])
def api_get_daily_business(
    hotel_id: int,
    start_date: str = None,
    end_date: str = None,
    session: Session = Depends(get_session),
):
    if start_date and end_date:
        from app.services.crud_business import get_daily_business_range
        return get_daily_business_range(session, hotel_id, start_date, end_date)
    else:
        from app.services.crud_business import get_monthly_business
        current_month = start_date[:7] if start_date else None
        if current_month:
            return get_monthly_business(session, hotel_id, current_month)
        return []


# ============ 竞品酒店 ============
@router.post("/competitors", response_model=CompetitorHotelResponse)
def api_create_competitor(data: CompetitorHotelCreate, session: Session = Depends(get_session)):
    competitor = CompetitorHotel(**data.model_dump())
    return create_competitor(session, competitor)


@router.get("/hotels/{hotel_id}/competitors", response_model=List[CompetitorHotelResponse])
def api_get_competitors(hotel_id: int, session: Session = Depends(get_session)):
    return get_competitors(session, hotel_id)


# ============ 竞品价格 ============
@router.post("/competitor-prices", response_model=CompetitorPriceResponse)
def api_create_competitor_price(data: CompetitorPriceCreate, session: Session = Depends(get_session)):
    price = CompetitorPrice(**data.model_dump())
    return create_competitor_price(session, price)


@router.get(
    "/competitors/{competitor_id}/prices",
    response_model=List[CompetitorPriceResponse],
)
def api_get_competitor_prices(
    competitor_id: int,
    start_date: str = None,
    end_date: str = None,
    session: Session = Depends(get_session),
):
    return get_competitor_prices(session, competitor_id, start_date, end_date)
