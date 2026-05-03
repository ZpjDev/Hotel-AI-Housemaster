from typing import List
from app.services.external_api.base_provider import OTADataProvider, CompetitorPriceData
from app.services.crud_competitor import create_competitor_price
from app.models import CompetitorPrice
from sqlmodel import Session


class OTADataService:
    """竞品价格数据服务"""

    def __init__(self, db_session: Session, provider: OTADataProvider = None):
        self.db = db_session
        self.provider = provider
        if not provider:
            from app.services.external_api.mock_ota_provider import MockOTAProvider
            self.provider = MockOTAProvider()

    async def sync_competitor_prices(
        self, hotel_id: int, days: List[int] = None
    ) -> List[CompetitorPrice]:
        """同步竞品价格"""
        from datetime import datetime, timedelta

        from app.services.crud_competitor import get_competitors

        competitors = get_competitors(self.db, hotel_id)
        if not days:
            days = [0, 1, 2, 3, 5, 7, 15, 30]

        today = datetime.now().date()
        all_prices = []

        for competitor in competitors:
            dates = [(today + timedelta(days=d)).strftime("%Y-%m-%d") for d in days]

            try:
                price_data_list = await self.provider.get_competitor_prices(
                    competitor_id=competitor.id,
                    competitor_name=competitor.name,
                    dates=dates,
                )

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
                        data_source=self.provider.get_provider_name(),
                    )
                    saved = create_competitor_price(self.db, price_record)
                    all_prices.append(saved)
            except Exception as e:
                print(f"获取竞品 {competitor.name} 价格失败: {e}")
                continue

        return all_prices

    async def get_competitor_summary(self, hotel_id: int, date: str) -> str:
        """获取竞品数据摘要"""
        from app.services.crud_competitor import get_competitors, get_latest_competitor_price

        competitors = get_competitors(self.db, hotel_id)
        if not competitors:
            return "暂无竞品数据"

        summary_parts = []
        for comp in competitors:
            price = get_latest_competitor_price(self.db, comp.id, date)
            if price:
                status = "满房" if price.available_rooms == 0 else f"剩余{price.available_rooms}间"
                summary_parts.append(
                    f"{comp.name}: ¥{price.price}/晚, {status}, "
                    f"{'含早' if price.breakfast_included else '不含早'}"
                )
            else:
                summary_parts.append(f"{comp.name}: 暂无价格数据")

        return "\n".join(summary_parts)
