from fastapi import APIRouter, Depends, HTTPException
import time
from sqlmodel import Session
from app.database import get_session
from app.schemas import (
    CompetitorSyncRequest,
    CompetitorSyncResponse,
    OTADryRunRequest,
    OTADryRunResponse,
    OTADryRunMappedField,
)
from app.services.external_api.mock_ota_provider import MockOTAProvider
from app.services.external_api.third_party_ota_provider import ThirdPartyOTAProvider
from app.services.external_api.official_ota_provider import OfficialOTAProvider
from app.services.external_api.manual_provider import ManualOTAProvider
from app.services.crud_competitor import get_competitors, create_competitor_price
from app.models import CompetitorPrice
from datetime import datetime, timedelta
import logging
from app.utils.api_log import log_api_call

logger = logging.getLogger(__name__)

router = APIRouter()


def get_ota_provider(provider_name: str):
    """根据名称获取 OTA Provider"""
    providers = {
        "mock": MockOTAProvider,
        "manual": ManualOTAProvider,
        "third_party": ThirdPartyOTAProvider,
        "official": OfficialOTAProvider,
    }
    cls = providers.get(provider_name, MockOTAProvider)
    return cls()


@router.post("/external/ota-dry-run", response_model=OTADryRunResponse)
async def api_ota_dry_run(request: OTADryRunRequest):
    """真实 OTA API dry-run 测试

    只调用真实 API，不写入数据库。
    返回原始响应的脱敏摘要和字段映射后的结果。
    所有调用记录写入 APILog，不记录完整 API Key。
    """
    provider = get_ota_provider(request.provider)
    start_time = time.time()

    try:
        price_data_list = await provider.get_competitor_prices(
            competitor_id=request.competitor_id,
            competitor_name="",
            dates=[request.target_date],
        )
        latency = (time.time() - start_time) * 1000

        mapped_fields = []
        for pd in price_data_list:
            mapped_fields.append(OTADryRunMappedField(
                date=pd.date,
                price=pd.price,
                available_rooms=pd.available_rooms,
                is_bookable=pd.is_bookable,
                breakfast_included=pd.breakfast_included,
                platform=pd.platform,
                room_type=pd.room_type,
                remaining_rooms=pd.remaining_rooms,
                availability_status=pd.availability_status,
                cancellable=pd.cancellable,
                promotion_text=pd.promotion_text,
                source_type=pd.source_type,
                captured_at=pd.captured_at,
            ))

        raw_summary = {
            "competitor_id": request.competitor_id,
            "target_date": request.target_date,
            "mapped_count": len(mapped_fields),
            "provider": provider.get_provider_name(),
        }

        log_api_call(
            provider=provider.get_provider_name(),
            endpoint="/external/ota-dry-run",
            request_data={
                "competitor_id": request.competitor_id,
                "target_date": request.target_date,
            },
            response_data={
                "dry_run": True,
                "mapped_count": len(mapped_fields),
            },
            success=True,
            latency_ms=round(latency, 2),
        )

        return OTADryRunResponse(
            success=True,
            provider=provider.get_provider_name(),
            raw_summary=raw_summary,
            mapped_fields=mapped_fields,
            latency_ms=round(latency, 2),
        )

    except Exception as e:
        latency = (time.time() - start_time) * 1000

        log_api_call(
            provider=provider.get_provider_name(),
            endpoint="/external/ota-dry-run",
            request_data={
                "competitor_id": request.competitor_id,
                "target_date": request.target_date,
            },
            success=False,
            error_message=str(e),
            latency_ms=round(latency, 2),
        )

        return OTADryRunResponse(
            success=False,
            provider=provider.get_provider_name(),
            raw_summary={
                "competitor_id": request.competitor_id,
                "target_date": request.target_date,
            },
            mapped_fields=[],
            error=str(e),
            latency_ms=round(latency, 2),
        )


@router.post("/external/competitor-sync", response_model=CompetitorSyncResponse)
async def api_competitor_sync(
    request: CompetitorSyncRequest,
    session: Session = Depends(get_session),
):
    """同步竞品价格"""
    provider = get_ota_provider(request.provider)

    competitors = get_competitors(session, request.hotel_id)
    if not competitors:
        return CompetitorSyncResponse(
            hotel_id=request.hotel_id,
            synced_count=0,
            failed_count=0,
            provider=request.provider,
            message="该酒店暂无竞品配置",
        )

    today = datetime.now().date()
    synced = 0
    failed = 0

    for comp in competitors:
        dates = [(today + timedelta(days=d)).strftime("%Y-%m-%d") for d in request.date_range]
        start_time = time.time()

        try:
            price_data_list = await provider.get_competitor_prices(
                competitor_id=comp.id,
                competitor_name=comp.name,
                dates=dates,
            )
            latency = (time.time() - start_time) * 1000

            for pd in price_data_list:
                price_record = CompetitorPrice(
                    competitor_id=pd.competitor_id,
                    date=pd.date,
                    price=pd.price,
                    available_rooms=pd.available_rooms,
                    is_bookable=pd.is_bookable,
                    breakfast_included=pd.breakfast_included,
                    cancellation_policy=pd.cancellation_policy,
                    promotion_info=pd.promotion_info,
                    data_source=provider.get_provider_name(),
                    platform=pd.platform,
                    room_type=pd.room_type,
                    remaining_rooms=pd.remaining_rooms,
                    availability_status=pd.availability_status,
                    cancellable=pd.cancellable,
                    promotion_text=pd.promotion_text,
                    source_type=pd.source_type,
                    captured_at=datetime.fromisoformat(pd.captured_at) if pd.captured_at else None,
                )
                create_competitor_price(session, price_record)
                synced += 1

            log_api_call(
                provider=provider.get_provider_name(),
                endpoint="/competitor/prices",
                request_data={"competitor_id": comp.id, "dates": dates},
                response_data={"synced": len(price_data_list)},
                success=True,
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            log_api_call(
                provider=provider.get_provider_name(),
                endpoint="/competitor/prices",
                request_data={"competitor_id": comp.id, "dates": dates},
                success=False,
                error_message=str(e),
                latency_ms=round(latency, 2),
            )
            logger.error(f"竞品 {comp.name} 同步失败: {e}")
            failed += 1

            if provider.get_provider_name() != "mock_ota_provider":
                try:
                    mock = MockOTAProvider()
                    mock_start = time.time()
                    price_data_list = await mock.get_competitor_prices(
                        competitor_id=comp.id,
                        competitor_name=comp.name,
                        dates=dates,
                    )
                    mock_latency = (time.time() - mock_start) * 1000

                    log_api_call(
                        provider="mock_ota_provider",
                        endpoint="/competitor/prices/fallback",
                        request_data={"competitor_id": comp.id},
                        response_data={"synced": len(price_data_list)},
                        success=True,
                        latency_ms=round(mock_latency, 2),
                    )

                    for pd in price_data_list:
                        price_record = CompetitorPrice(
                            competitor_id=pd.competitor_id,
                            date=pd.date,
                            price=pd.price,
                            available_rooms=pd.available_rooms,
                            is_bookable=pd.is_bookable,
                            breakfast_included=pd.breakfast_included,
                            data_source="mock_fallback",
                        )
                        create_competitor_price(session, price_record)
                        synced += 1
                except Exception as e2:
                    logger.error(f"竞品 {comp.name} mock 兜底也失败: {e2}")
                    failed += 1

    return CompetitorSyncResponse(
        hotel_id=request.hotel_id,
        synced_count=synced,
        failed_count=failed,
        provider=provider.get_provider_name(),
        message=f"成功同步 {synced} 条，失败 {failed} 条",
    )
