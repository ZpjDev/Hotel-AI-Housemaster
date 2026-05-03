from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.database import get_session
from app.services.crud_hotel import get_hotel, get_hotels
from app.services.crud_competitor import get_competitors
from app.services.crud_room_type import get_room_types
from app.services.crud_others import get_api_configs, get_pending_actions, get_ota_orders
from app.services.crud_business import get_daily_business_range
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request, session: Session = Depends(get_session)):
    hotels = get_hotels(session)
    return templates.TemplateResponse(
        request,
        "admin/index.html",
        context={"hotels": hotels},
    )


@router.get("/admin/hotels/{hotel_id}/competitors", response_class=HTMLResponse)
async def admin_competitors(
    request: Request,
    hotel_id: int,
    session: Session = Depends(get_session),
):
    hotel = get_hotel(session, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="酒店不存在")
    competitors = get_competitors(session, hotel_id)
    return templates.TemplateResponse(
        request,
        "admin/competitors.html",
        context={"hotel": hotel, "competitors": competitors},
    )


@router.get("/admin/hotels/{hotel_id}/room-types", response_class=HTMLResponse)
async def admin_room_types(
    request: Request,
    hotel_id: int,
    session: Session = Depends(get_session),
):
    hotel = get_hotel(session, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="酒店不存在")
    room_types = get_room_types(session, hotel_id)
    return templates.TemplateResponse(
        request,
        "admin/room_types.html",
        context={"hotel": hotel, "room_types": room_types},
    )


@router.get("/admin/api-settings", response_class=HTMLResponse)
async def admin_api_settings(request: Request, session: Session = Depends(get_session)):
    configs = get_api_configs(session)
    return templates.TemplateResponse(
        request,
        "admin/api_settings.html",
        context={"configs": configs},
    )


@router.get("/admin/api-settings/test/{key}")
async def admin_test_api(key: str, session: Session = Depends(get_session)):
    from app.services.ai_provider import AIProvider, decrypt_value, get_ai_config, get_ota_config, get_wechat_config, get_phone_config
    from app.services.external_api.mock_ota_provider import MockOTAProvider
    from app.services.crud_others import get_api_config

    config = get_api_config(session, key)
    if not config:
        return {"status": "error", "message": "配置不存在"}

    raw_value = decrypt_value(config.value) if config.is_encrypted else config.value

    if key == "ai_api_base":
        ai = AIProvider(api_base=raw_value)
        result = await ai.test_connection()
        return result
    elif key == "ai_api_key":
        ai_cfg = get_ai_config()
        ai = AIProvider(api_key=raw_value, api_base=ai_cfg["api_base"], model=ai_cfg["model"])
        result = await ai.test_connection()
        return result
    elif key == "ota_api_base":
        ota_cfg = get_ota_config()
        from app.services.external_api.base_provider import OTADataProvider
        class TestOTA(OTADataProvider):
            async def get_competitor_prices(self, *args, **kwargs): return []
            async def test_connection(self): return {"status": "ok", "message": f"OTA API Base: {ota_cfg['api_base']}"}
            def get_provider_name(self): return "test_ota"
        ota = TestOTA()
        return await ota.test_connection()
    elif key == "ota_api_key":
        return {"status": "ok", "message": "OTA API Key 已配置" if raw_value else "OTA API Key 未配置"}
    elif key == "wechat_app_secret":
        wc = get_wechat_config()
        if wc["app_id"] and raw_value:
            from app.services.wechat.wechat_provider import OfficialWechatProvider
            provider = OfficialWechatProvider(app_id=wc["app_id"], app_secret=raw_value, token=wc["token"])
            return await provider.test_connection()
        return {"status": "info", "message": "微信配置不完整"}
    elif key in ["wechat_app_id", "wechat_token", "wechat_encoding_aes_key"]:
        return {"status": "ok", "message": f"{key} 已配置" if raw_value else f"{key} 未配置"}
    elif key == "phone_api_key":
        return {"status": "ok", "message": "电话 API Key 已配置" if raw_value else "电话 API Key 未配置"}
    elif key == "phone_api_base":
        phone_cfg = get_phone_config()
        return {"status": "ok", "message": f"电话 API Base: {phone_cfg['api_base'] or '未配置'}"}
    elif key == "notify_webhook_url":
        from app.services.external_api.notify_provider import WebhookNotifyProvider
        provider = WebhookNotifyProvider(webhook_url=raw_value)
        return await provider.test_connection()
    else:
        return {"status": "info", "message": f"测试 {key} 连接成功，值已脱敏: {raw_value[:8]}****" if raw_value else "未配置"}


@router.get("/admin/pending-actions", response_class=HTMLResponse)
async def admin_pending_actions(
    request: Request,
    hotel_id: int = None,
    session: Session = Depends(get_session),
):
    actions = get_pending_actions(session, hotel_id=hotel_id)
    return templates.TemplateResponse(
        request,
        "admin/pending_actions.html",
        context={"actions": actions},
    )


@router.get("/admin/hotels/{hotel_id}/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    hotel_id: int,
    session: Session = Depends(get_session),
):
    hotel = get_hotel(session, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="酒店不存在")
    orders = get_ota_orders(session, hotel_id)
    return templates.TemplateResponse(
        request,
        "admin/orders.html",
        context={"hotel": hotel, "orders": orders},
    )


@router.get("/admin/hotels/{hotel_id}/room-calendar", response_class=HTMLResponse)
async def admin_room_calendar(
    request: Request,
    hotel_id: int,
    month: str = None,
    session: Session = Depends(get_session),
):
    from datetime import datetime, timedelta
    hotel = get_hotel(session, hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="酒店不存在")

    if month:
        target = datetime.strptime(month, "%Y-%m")
    else:
        target = datetime.now()

    year, mon = target.year, target.month
    import calendar
    first_day = datetime(year, mon, 1)
    last_day = datetime(year, mon, calendar.monthrange(year, mon)[1])

    # 生成月份选择列表（前后3个月）
    months = []
    for i in range(-2, 4):
        m = mon + i
        y = year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        label = f"{y}年{m}月"
        value = f"{y}-{m:02d}"
        selected = (m == mon and y == year)
        months.append({"label": label, "value": value, "selected": selected})

    # 获取该月经营数据
    business_data = {}
    all_business = get_daily_business_range(session, hotel_id, str(first_day.date()), str(last_day.date()))
    for b in all_business:
        business_data[b.date] = b

    # 构建日历天数
    today = datetime.now().date()
    start_weekday = first_day.weekday()
    calendar_days = []

    for _ in range(start_weekday):
        calendar_days.append({"is_empty": True})

    current = first_day
    while current <= last_day:
        date_str = current.strftime("%Y-%m-%d")
        b = business_data.get(date_str)
        cal_day = {
            "is_empty": False,
            "day": current.day,
            "is_today": (current.date() == today),
            "business": None,
        }
        if b:
            cal_day["business"] = {
                "sold_rooms": b.sold_rooms,
                "total_rooms": b.total_rooms,
                "total_revenue": b.total_revenue,
                "occupancy_rate": round(b.occupancy_rate, 1),
            }
        calendar_days.append(cal_day)
        current += timedelta(days=1)

    # 统计
    total_days_with_data = len(all_business)
    avg_occupancy = round(sum(b.occupancy_rate for b in all_business) / total_days_with_data, 1) if total_days_with_data else 0
    avg_price = round(sum(b.adr for b in all_business if b.adr > 0) / max(1, sum(1 for b in all_business if b.adr > 0)), 0) if all_business else 0
    total_revenue = round(sum(b.total_revenue for b in all_business), 0)

    stats = {
        "total_rooms": hotel.total_rooms,
        "avg_occupancy": avg_occupancy,
        "avg_price": int(avg_price),
        "total_revenue": int(total_revenue),
    }

    return templates.TemplateResponse(
        request,
        "admin/room_calendar.html",
        context={
            "hotel": hotel,
            "calendar_days": calendar_days,
            "stats": stats,
            "months": months,
        },
    )


@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, session: Session = Depends(get_session)):
    configs = get_api_configs(session)
    return templates.TemplateResponse(
        request,
        "admin/settings.html",
        context={"configs": configs},
    )


@router.get("/admin/monitor", response_class=HTMLResponse)
async def admin_monitor(request: Request):
    return templates.TemplateResponse(
        request,
        "admin/monitor.html",
    )
