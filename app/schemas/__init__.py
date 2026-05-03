from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============ 酒店 ============
class HotelCreate(BaseModel):
    name: str
    city: str
    address: str
    phone: str
    total_rooms: int
    boss_openid: str
    description: Optional[str] = None
    check_in_time: str = "14:00"
    check_out_time: str = "12:00"
    has_parking: bool = True
    has_breakfast: bool = True
    allow_pets: bool = False
    wifi_info: Optional[str] = None


class HotelUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    total_rooms: Optional[int] = None
    boss_openid: Optional[str] = None
    description: Optional[str] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    has_parking: Optional[bool] = None
    has_breakfast: Optional[bool] = None
    allow_pets: Optional[bool] = None
    wifi_info: Optional[str] = None


class HotelResponse(BaseModel):
    id: int
    name: str
    city: str
    address: str
    phone: str
    total_rooms: int
    boss_openid: str
    description: Optional[str]
    check_in_time: str
    check_out_time: str
    has_parking: bool
    has_breakfast: bool
    allow_pets: bool
    wifi_info: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 房型 ============
class RoomTypeCreate(BaseModel):
    hotel_id: int
    name: str
    total_count: int
    base_price: float
    min_price: float
    max_price: float
    features: Optional[str] = None
    breakfast_included: bool = False
    cancellation_policy: Optional[str] = None


class RoomTypeUpdate(BaseModel):
    name: Optional[str] = None
    total_count: Optional[int] = None
    base_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    features: Optional[str] = None
    breakfast_included: Optional[bool] = None
    cancellation_policy: Optional[str] = None


class RoomTypeResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    total_count: int
    base_price: float
    min_price: float
    max_price: float
    features: Optional[str]
    breakfast_included: bool
    cancellation_policy: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 经营数据 ============
class DailyBusinessCreate(BaseModel):
    hotel_id: int
    date: str
    total_rooms: int
    sold_rooms: int
    available_rooms: Optional[int] = None
    total_revenue: float
    ota_orders: int
    direct_orders: int


class DailyBusinessResponse(BaseModel):
    id: int
    hotel_id: int
    date: str
    total_rooms: int
    sold_rooms: int
    available_rooms: int
    occupancy_rate: float
    adr: float
    revpar: float
    total_revenue: float
    ota_orders: int
    direct_orders: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 竞品酒店 ============
class CompetitorHotelCreate(BaseModel):
    hotel_id: int
    name: str
    platform: str
    address: str
    distance_km: float
    url: Optional[str] = None
    weight: int = 1


class CompetitorHotelResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    platform: str
    address: str
    distance_km: float
    url: Optional[str]
    weight: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 竞品价格 ============
class CompetitorPriceCreate(BaseModel):
    competitor_id: int
    date: str
    price: float
    available_rooms: int
    is_bookable: bool = True
    breakfast_included: bool = False
    cancellation_policy: Optional[str] = None
    promotion_info: Optional[str] = None
    data_source: str = "mock"


class CompetitorPriceResponse(BaseModel):
    id: int
    competitor_id: int
    date: str
    price: float
    available_rooms: int
    is_bookable: bool
    breakfast_included: bool
    cancellation_policy: Optional[str]
    promotion_info: Optional[str]
    data_source: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ AI 策略 (JSON 输出) ============
class SuggestedPriceItem(BaseModel):
    room_type: str
    min_price: float
    max_price: float
    reason: str


class ActionRequiredItem(BaseModel):
    action: str
    type: str
    reason: str


class StrategyRequest(BaseModel):
    hotel_id: int
    target_date: Optional[str] = None
    time_slot: Optional[str] = None
    question: Optional[str] = None


class StrategyResponse(BaseModel):
    hotel_id: int
    date: str
    time_slot: str
    market_analysis: str
    competitor_analysis: str
    suggested_prices: List[SuggestedPriceItem]
    suggested_price: str
    room_control_strategy: str
    ota_strategy: str
    promotion_strategy: str
    direct_customer_strategy: str
    risk_alert: str
    actions_required: List[ActionRequiredItem]
    full_report: str


class WechatWebhookRequest(BaseModel):
    ToUserName: str
    FromUserName: str
    CreateTime: int
    MsgType: str = "text"
    Content: Optional[str] = None


# ============ 月报 ============
class MonthlyReportRequest(BaseModel):
    hotel_id: int
    month: str


class MonthlyReportResponse(BaseModel):
    hotel_id: int
    month: str
    report: str


# ============ 客户 ============
class CustomerCreate(BaseModel):
    hotel_id: int
    name: str
    wechat_id: Optional[str] = None
    phone: Optional[str] = None
    source: str = "ota"
    tags: Optional[str] = None
    preferences: Optional[str] = None


class CustomerResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    wechat_id: Optional[str]
    phone: Optional[str]
    source: str
    tags: Optional[str]
    preferences: Optional[str]
    stay_count: int
    last_stay_date: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 点评 ============
class ReviewCreate(BaseModel):
    hotel_id: int
    customer_id: Optional[int] = None
    platform: str
    rating: int
    content: str


class ReviewResponse(BaseModel):
    id: int
    hotel_id: int
    customer_id: Optional[int]
    platform: str
    rating: int
    content: str
    reply_content: Optional[str]
    reply_status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 订单 ============
class OTAOrderCreate(BaseModel):
    hotel_id: int
    platform: str
    order_no: str
    customer_name: str
    customer_phone: str
    room_type: str
    check_in_date: str
    check_out_date: str
    amount: float
    status: str = "pending"


class OTAOrderResponse(BaseModel):
    id: int
    hotel_id: int
    platform: str
    order_no: str
    customer_name: str
    customer_phone: str
    room_type: str
    check_in_date: str
    check_out_date: str
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 待确认动作 ============
class PendingActionCreate(BaseModel):
    hotel_id: int
    action_type: str
    platform: Optional[str] = None
    payload_json: str = "{}"
    risk_level: str = "medium"
    ai_reason: Optional[str] = None


class PendingActionResponse(BaseModel):
    id: int
    hotel_id: int
    action_type: str
    platform: Optional[str]
    payload_json: str
    risk_level: str
    ai_reason: Optional[str]
    status: str
    created_at: datetime
    approved_at: Optional[datetime]
    executed_at: Optional[datetime]
    failed_reason: Optional[str]
    model_config = ConfigDict(from_attributes=True)


# ============ API 配置 ============
class APIConfigCreate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    is_encrypted: bool = True


class APIConfigUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None


class APIConfigResponse(BaseModel):
    id: int
    key: str
    value: str = ""
    masked_value: Optional[str] = None
    description: Optional[str]
    is_encrypted: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 知识库 ============
class KnowledgeBaseCreate(BaseModel):
    hotel_id: int
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


class KnowledgeBaseUpdate(BaseModel):
    hotel_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    checkin_time: Optional[str] = None
    checkout_time: Optional[str] = None
    parking_info: Optional[str] = None
    breakfast_info: Optional[str] = None
    pet_policy: Optional[str] = None
    invoice_policy: Optional[str] = None
    cancellation_policy: Optional[str] = None
    nearby_transport: Optional[str] = None
    nearby_attractions: Optional[str] = None
    room_type_descriptions: Optional[str] = None
    wifi_info: Optional[str] = None
    other_faq: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: int
    hotel_id: int
    hotel_name: str
    address: str
    phone: str
    checkin_time: str
    checkout_time: str
    parking_info: Optional[str]
    breakfast_info: Optional[str]
    pet_policy: Optional[str]
    invoice_policy: Optional[str]
    cancellation_policy: Optional[str]
    nearby_transport: Optional[str]
    nearby_attractions: Optional[str]
    room_type_descriptions: Optional[str]
    wifi_info: Optional[str]
    other_faq: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============ 竞品同步 ============
class CompetitorSyncRequest(BaseModel):
    hotel_id: int
    date_range: List[int] = [0, 1, 2, 3, 5, 7, 15, 30]
    provider: str = "mock"


class CompetitorSyncResponse(BaseModel):
    hotel_id: int
    synced_count: int
    failed_count: int
    provider: str
    message: str


# ============ OTA Dry Run ============
class OTADryRunRequest(BaseModel):
    hotel_id: int
    competitor_id: int
    target_date: str
    provider: str = "third_party"


class OTADryRunMappedField(BaseModel):
    date: str
    price: float
    available_rooms: int
    is_bookable: bool
    breakfast_included: bool
    platform: Optional[str]
    room_type: Optional[str]
    remaining_rooms: Optional[int]
    availability_status: Optional[str]
    cancellable: Optional[bool]
    promotion_text: Optional[str]
    source_type: Optional[str]
    captured_at: Optional[str]


class OTADryRunResponse(BaseModel):
    success: bool
    provider: str
    raw_summary: dict
    mapped_fields: List[OTADryRunMappedField]
    error: Optional[str] = None
    latency_ms: float
