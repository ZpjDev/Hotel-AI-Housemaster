from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Hotel(SQLModel, table=True):
    __tablename__ = "hotels"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    city: str
    address: str
    phone: str
    total_rooms: int
    boss_openid: str = Field(index=True)
    description: Optional[str] = None
    check_in_time: str = "14:00"
    check_out_time: str = "12:00"
    has_parking: bool = True
    has_breakfast: bool = True
    allow_pets: bool = False
    wifi_info: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class RoomType(SQLModel, table=True):
    __tablename__ = "room_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    name: str
    total_count: int
    base_price: float
    min_price: float
    max_price: float
    features: Optional[str] = None
    breakfast_included: bool = False
    cancellation_policy: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class DailyBusiness(SQLModel, table=True):
    __tablename__ = "daily_business"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    date: str = Field(index=True)
    total_rooms: int
    sold_rooms: int
    available_rooms: int
    occupancy_rate: float
    adr: float
    revpar: float
    total_revenue: float
    ota_orders: int
    direct_orders: int
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CompetitorHotel(SQLModel, table=True):
    __tablename__ = "competitor_hotels"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    name: str
    platform: str
    address: str
    distance_km: float
    url: Optional[str] = None
    weight: int = Field(default=1)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CompetitorPrice(SQLModel, table=True):
    __tablename__ = "competitor_prices"

    id: Optional[int] = Field(default=None, primary_key=True)
    competitor_id: int = Field(foreign_key="competitor_hotels.id", index=True)
    date: str = Field(index=True)
    price: float
    available_rooms: int
    is_bookable: bool = True
    breakfast_included: bool = False
    cancellation_policy: Optional[str] = None
    promotion_info: Optional[str] = None
    data_source: str = "mock"
    platform: Optional[str] = None
    room_type: Optional[str] = None
    remaining_rooms: Optional[int] = None
    availability_status: Optional[str] = None
    cancellable: Optional[bool] = None
    promotion_text: Optional[str] = None
    source_type: Optional[str] = None
    captured_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StrategyReport(SQLModel, table=True):
    __tablename__ = "strategy_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    date: str = Field(index=True)
    time_slot: str
    question: Optional[str] = None
    market_analysis: Optional[str] = None
    competitor_analysis: Optional[str] = None
    suggested_price: Optional[str] = None
    suggested_prices_json: Optional[str] = None
    room_control_strategy: Optional[str] = None
    ota_strategy: Optional[str] = None
    promotion_strategy: Optional[str] = None
    direct_customer_strategy: Optional[str] = None
    risk_alert: Optional[str] = None
    actions_required_json: Optional[str] = None
    full_report: str
    created_at: datetime = Field(default_factory=datetime.now)


class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    name: str
    wechat_id: Optional[str] = None
    phone: Optional[str] = None
    source: str = "ota"
    tags: Optional[str] = None
    preferences: Optional[str] = None
    stay_count: int = Field(default=1)
    last_stay_date: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    customer_id: Optional[int] = None
    platform: str
    rating: int
    content: str
    reply_content: Optional[str] = None
    reply_status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class OTAOrder(SQLModel, table=True):
    __tablename__ = "ota_orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    platform: str
    order_no: str = Field(index=True)
    customer_name: str
    customer_phone: str
    room_type: str
    check_in_date: str
    check_out_date: str
    amount: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PendingAction(SQLModel, table=True):
    __tablename__ = "pending_actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    action_type: str
    platform: Optional[str] = None
    payload_json: str = "{}"
    risk_level: str = "medium"
    ai_reason: Optional[str] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    failed_reason: Optional[str] = None


class APIConfig(SQLModel, table=True):
    __tablename__ = "api_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: str
    description: Optional[str] = None
    is_encrypted: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class APILog(SQLModel, table=True):
    __tablename__ = "api_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    endpoint: str
    request_data: Optional[str] = None
    response_data: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    latency_ms: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)


class WechatMessage(SQLModel, table=True):
    __tablename__ = "wechat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True)
    openid: str
    message: str
    intent: Optional[str] = None
    response: Optional[str] = None
    strategy_report_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)


class KnowledgeBase(SQLModel, table=True):
    __tablename__ = "knowledge_base"

    id: Optional[int] = Field(default=None, primary_key=True)
    hotel_id: int = Field(foreign_key="hotels.id", index=True, unique=True)
    hotel_name: str
    address: str
    phone: str
    checkin_time: str = "14:00"
    checkout_time: str = "12:00"
    parking_info: Optional[str] = "提供免费停车位"
    breakfast_info: Optional[str] = "含早餐，7:00-10:00"
    pet_policy: Optional[str] = "暂不允许携带宠物"
    invoice_policy: Optional[str] = "可提供电子发票，请联系前台"
    cancellation_policy: Optional[str] = "入住前24小时可免费取消"
    nearby_transport: Optional[str] = "距离地铁站步行10分钟"
    nearby_attractions: Optional[str] = "距离西湖景区步行15分钟"
    room_type_descriptions: Optional[str] = None
    wifi_info: Optional[str] = "全区域免费WiFi"
    other_faq: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
