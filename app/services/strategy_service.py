import json
import logging
import time
from typing import Optional, List
from sqlmodel import Session
from datetime import datetime
from app.services.ai_provider import AIProvider
from app.services.external_api.ota_data_service import OTADataService
from app.services.crud_hotel import get_hotel
from app.services.crud_room_type import get_room_types
from app.services.crud_business import get_daily_business
from app.services.crud_competitor import get_competitors
from app.services.crud_others import create_pending_action
from app.models import PendingAction

logger = logging.getLogger(__name__)


class StrategyService:
    """AI 经营策略服务 - 强制 JSON 输出"""

    def __init__(self, db: Session, ai_provider: AIProvider, ota_service: OTADataService):
        self.db = db
        self.ai = ai_provider
        self.ota = ota_service

    async def generate_strategy(
        self,
        hotel_id: int,
        target_date: str = None,
        time_slot: str = None,
        question: str = None,
    ) -> dict:
        """生成经营策略（JSON 格式）"""
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")
        if not time_slot:
            time_slot = datetime.now().strftime("%H:%M")

        hotel = get_hotel(self.db, hotel_id)
        if not hotel:
            raise ValueError(f"酒店 {hotel_id} 不存在")

        room_types = get_room_types(self.db, hotel_id)
        business = get_daily_business(self.db, hotel_id, target_date)
        competitors = get_competitors(self.db, hotel_id)
        competitor_summary = await self.ota.get_competitor_summary(hotel_id, target_date)

        available_rooms = hotel.total_rooms
        sold_rooms = 0
        occupancy_rate = 0.0
        adr = 0.0
        revpar = 0.0
        revenue = 0.0

        if business:
            available_rooms = business.available_rooms
            sold_rooms = business.sold_rooms
            occupancy_rate = business.occupancy_rate
            adr = business.adr
            revpar = business.revpar
            revenue = business.total_revenue

        room_summary = ""
        room_type_names = []
        for rt in room_types:
            room_summary += f"- {rt.name}: {rt.total_count}间, 基础价¥{rt.base_price}, 范围¥{rt.min_price}-¥{rt.max_price}\n"
            room_type_names.append(rt.name)

        room_info = {
            "hotel_name": hotel.name,
            "city": hotel.city,
            "total_rooms": hotel.total_rooms,
            "available_rooms": available_rooms,
            "sold_rooms": sold_rooms,
            "occupancy_rate": occupancy_rate,
            "adr": adr,
            "revpar": revpar,
            "revenue": revenue,
            "room_types": room_summary,
            "room_type_names": room_type_names,
            "competitors": competitor_summary,
            "target_date": target_date,
        }

        prompt = self._build_json_strategy_prompt(room_info, question)

        try:
            ai_response = await self.ai.chat_completion([
                {"role": "system", "content": "你是一位资深酒店经营策略顾问。你必须输出纯 JSON 格式，不要包含任何其他文字。"},
                {"role": "user", "content": prompt},
            ])

            parsed = self._parse_json_response(ai_response, room_type_names)
        except Exception as e:
            logger.warning(f"AI JSON 解析失败，使用规则策略: {e}")
            parsed = self._rule_based_strategy(room_info, room_type_names)

        return {
            "hotel_id": hotel_id,
            "date": target_date,
            "time_slot": time_slot,
            "market_analysis": parsed.get("market_analysis", ""),
            "competitor_analysis": parsed.get("competitor_analysis", ""),
            "suggested_prices": parsed.get("suggested_prices", []),
            "suggested_price": parsed.get("suggested_price", ""),
            "room_control_strategy": parsed.get("room_control_strategy", ""),
            "ota_strategy": parsed.get("ota_strategy", ""),
            "promotion_strategy": parsed.get("promotion_strategy", ""),
            "direct_customer_strategy": parsed.get("direct_customer_strategy", ""),
            "risk_alert": parsed.get("risk_alert", ""),
            "actions_required": parsed.get("actions_required", []),
            "full_report": parsed.get("full_report", ""),
        }

    def _build_json_strategy_prompt(self, room_info: dict, question: str) -> str:
        """构建 JSON 格式策略提示词"""
        available = room_info["available_rooms"]
        total = room_info["total_rooms"]
        occupancy = room_info["occupancy_rate"]
        date = room_info["target_date"]

        prompt = f"""你正在为 {room_info['hotel_name']}（{room_info['city']}）提供 {date} 的经营策略建议。

【自家经营数据】
- 总房量：{total} 间
- 已售：{room_info['sold_rooms']} 间
- 剩余：{available} 间
- 入住率：{occupancy}%
- ADR：¥{room_info['adr']}
- RevPAR：¥{room_info['revpar']}

【房型信息】
{room_info['room_types']}

【竞品情况】
{room_info['competitors']}
"""

        if question:
            prompt += f"\n老板的问题：{question}\n"

        prompt += f"""
请根据以上数据，输出以下 JSON 格式的经营策略建议（必须纯 JSON，不要包含 markdown 格式）：

{{
  "market_analysis": "当前整体市场需求判断（2-3句）",
  "competitor_analysis": "竞品价格区间、房态对比分析",
  "suggested_prices": [
    {{
      "room_type": "房型名称",
      "min_price": 268,
      "max_price": 298,
      "reason": "定价理由"
    }}
  ],
  "suggested_price": "综合建议价格区间描述",
  "room_control_strategy": "如何合理分配房间",
  "ota_strategy": "在OTA平台的具体操作建议",
  "promotion_strategy": "是否需要促销活动，具体什么活动",
  "direct_customer_strategy": "如何引导直客下单",
  "risk_alert": "需要注意的风险",
  "actions_required": [
    {{
      "action": "具体操作",
      "type": "pricing/inventory/order/promotion",
      "reason": "原因"
    }}
  ],
  "full_report": "完整策略报告（包含以上所有内容的详细文本，不少于200字）"
}}

注意：
- 如果自家剩余房少（{available}间）、入住率高（{occupancy}%），建议适度涨价
- 如果自家剩余房多、竞品低价多，建议小幅降价或限时促销
- 如果竞品普遍满房，建议提高价格并减少低价促销
- 如果当天晚上仍有大量空房，建议尾房策略
- 每个房型都要给出具体价格区间
- suggested_prices 中必须包含房型：{", ".join(room_info.get("room_type_names", []))}
"""

        return prompt

    def _parse_json_response(self, ai_response: str, room_type_names: List[str]) -> dict:
        """解析 AI JSON 响应"""
        cleaned = ai_response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        data = json.loads(cleaned)

        if "suggested_prices" not in data or not data["suggested_prices"]:
            data["suggested_prices"] = []
            for name in room_type_names:
                data["suggested_prices"].append({
                    "room_type": name,
                    "min_price": 250,
                    "max_price": 350,
                    "reason": "建议根据市场情况调整",
                })

        if "suggested_price" not in data:
            prices = data.get("suggested_prices", [])
            if prices:
                min_p = min(p.get("min_price", 0) for p in prices)
                max_p = max(p.get("max_price", 0) for p in prices)
                data["suggested_price"] = f"¥{min_p:.0f}-¥{max_p:.0f}"

        if "actions_required" not in data:
            data["actions_required"] = []

        if "full_report" not in data:
            data["full_report"] = ai_response

        return data

    def _rule_based_strategy(self, room_info: dict, room_type_names: List[str]) -> dict:
        """规则引擎策略（AI JSON 解析失败时的 fallback）"""
        available = room_info["available_rooms"]
        total = room_info["total_rooms"]
        occupancy = room_info["occupancy_rate"]
        adr = room_info["adr"]

        if occupancy >= 90 or available <= 3:
            pricing_direction = "供不应求，建议涨价10-20%"
            price_multiplier = 1.15
        elif occupancy >= 70:
            pricing_direction = "供需平衡，建议保持现价或微调"
            price_multiplier = 1.0
        elif occupancy >= 50:
            pricing_direction = "需求偏弱，建议降价5-10%或限时促销"
            price_multiplier = 0.9
        else:
            pricing_direction = "需求较弱，建议降价10-20%或尾房促销"
            price_multiplier = 0.8

        suggested_prices = []
        base_price = adr if adr > 0 else 300

        for name in room_type_names:
            min_p = round(base_price * price_multiplier * 0.85, 0)
            max_p = round(base_price * price_multiplier * 1.15, 0)
            suggested_prices.append({
                "room_type": name,
                "min_price": int(min_p),
                "max_price": int(max_p),
                "reason": pricing_direction,
            })

        min_overall = int(min(p["min_price"] for p in suggested_prices))
        max_overall = int(max(p["max_price"] for p in suggested_prices))

        return {
            "market_analysis": f"当前入住率{occupancy}%，剩余{available}间。{pricing_direction}",
            "competitor_analysis": room_info.get("competitors", "暂无竞品数据"),
            "suggested_prices": suggested_prices,
            "suggested_price": f"¥{min_overall}-¥{max_overall}",
            "room_control_strategy": f"剩余{available}间，建议：1）优先保留高价房型库存；2）低价房型可考虑升级促销",
            "ota_strategy": "建议在OTA平台提升排名，增加曝光。设置限时折扣吸引即时下单。",
            "promotion_strategy": "可设置：连住优惠、早鸟价、会员专享价等促销活动。",
            "direct_customer_strategy": "联系老客户和协议客户，提供专属优惠，引导直客下单。",
            "risk_alert": f"当前入住率{occupancy}%，需关注市场动态，避免过度降价影响品牌。",
            "actions_required": [
                {"action": f"将价格调整至 ¥{min_overall}-¥{max_overall}", "type": "pricing", "reason": "根据入住率和竞品数据调整"},
                {"action": "在OTA平台设置限时促销", "type": "promotion", "reason": "提升即时订单转化"},
            ],
            "full_report": f"""
# 经营策略报告

## 市场判断
当前入住率{occupancy}%，总房量{total}间，剩余{available}间。{pricing_direction}

## 建议价格
综合建议：¥{min_overall}-¥{max_overall}

## 房型价格
""",
        }
