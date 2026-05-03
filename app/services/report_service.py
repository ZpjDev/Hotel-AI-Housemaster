from app.services.crud_business import get_monthly_business
from app.services.crud_competitor import get_competitors, get_competitor_prices
from app.services.ai_provider import AIProvider
from sqlmodel import Session
from datetime import datetime


class ReportService:
    """月度经营报告服务"""

    def __init__(self, db: Session, ai_provider: AIProvider):
        self.db = db
        self.ai = ai_provider

    async def generate_monthly_report(self, hotel_id: int, month: str) -> str:
        """生成月度经营报告"""

        business_data = get_monthly_business(self.db, hotel_id, month)

        if not business_data:
            return f"# {month} 月度经营报告\n\n暂无经营数据，请先录入每日经营数据。"

        total_revenue = sum(b.total_revenue for b in business_data)
        total_sold = sum(b.sold_rooms for b in business_data)
        total_rooms = sum(b.total_rooms for b in business_data)
        avg_occupancy = sum(b.occupancy_rate for b in business_data) / len(business_data)
        avg_adr = sum(b.adr for b in business_data) / len(business_data)
        avg_revpar = sum(b.revpar for b in business_data) / len(business_data)
        total_ota = sum(b.ota_orders for b in business_data)
        total_direct = sum(b.direct_orders for b in business_data)

        peak_day = max(business_data, key=lambda x: x.sold_rooms)
        low_day = min(business_data, key=lambda x: x.sold_rooms)

        competitors = get_competitors(self.db, hotel_id)
        comp_price_summary = ""
        for comp in competitors:
            prices = get_competitor_prices(self.db, comp.id, f"{month}-01", f"{month}-31")
            if prices:
                avg_price = sum(p.price for p in prices) / len(prices)
                comp_price_summary += f"- {comp.name}: 月均价 ¥{avg_price:.0f}\n"

        if not comp_price_summary:
            comp_price_summary = "- 暂无竞品价格数据"

        prompt = f"""请根据以下数据生成 {month} 月度经营分析报告：

【营收概况】
- 本月总营收：¥{total_revenue:,.0f}
- 平均入住率：{avg_occupancy:.1f}%
- 平均 ADR：¥{avg_adr:.1f}
- 平均 RevPAR：¥{avg_revpar:.1f}
- 总售房数：{total_sold} 间
- OTA 订单：{total_ota} 单
- 直客订单：{total_direct} 单
- OTA 占比：{total_ota/(total_ota+total_direct)*100 if (total_ota+total_direct)>0 else 0:.1f}%
- 直客占比：{total_direct/(total_ota+total_direct)*100 if (total_ota+total_direct)>0 else 0:.1f}%

【高峰与低谷】
- 高峰日期：{peak_day.date}（售出 {peak_day.sold_rooms} 间）
- 低谷日期：{low_day.date}（售出 {low_day.sold_rooms} 间）

【竞品价格】
{comp_price_summary}

请输出 Markdown 格式报告，包括：
1. 本月营收总结
2. 平均入住率、ADR、RevPAR 分析
3. OTA 与直客占比分析
4. 高峰/低谷分析
5. 竞品价格走势与自家价格位置
6. 下月定价建议
7. 渠道优化建议
8. 成本优化建议
9. 客户维护建议

要求数据具体，建议可操作。"""

        try:
            report = await self.ai.chat_completion([
                {"role": "system", "content": "你是一位酒店经营分析师，擅长撰写专业的月度经营报告。"},
                {"role": "user", "content": prompt},
            ])
        except Exception as e:
            report = f"# {month} 月度经营报告\n\n**数据摘要：**\n- 总营收：¥{total_revenue:,.0f}\n- 平均入住率：{avg_occupancy:.1f}%\n- 平均 ADR：¥{avg_adr:.1f}\n\nAI 报告生成失败：{e}"

        return report
