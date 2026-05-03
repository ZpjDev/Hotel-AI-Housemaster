from typing import Optional


class IntentDetector:
    """微信消息意图识别"""

    INTENT_MAP = {
        "pricing": ["定价", "价格", "多少钱", "调价", "涨价", "降价"],
        "room_status": ["房态", "剩余", "空房", "几间房", "几间空", "还有房"],
        "competitor": ["竞品", "对手", "附近", "周边", "竞争对手"],
        "report": ["报告", "月报", "总结", "经营情况", "经营分析"],
        "review_reply": ["差评", "点评", "回复", "评价", "评论"],
        "strategy": ["策略", "怎么办", "建议", "怎么", "如何", "帮我"],
        "greeting": ["你好", "早上好", "下午好", "晚上好", "嗨", "哈喽"],
        "monthly_report": ["月度", "月报", "本月报告", "月份"],
    }

    @classmethod
    def detect(cls, message: str) -> str:
        """检测用户消息意图"""
        message = message.lower()

        for intent, keywords in cls.INTENT_MAP.items():
            for keyword in keywords:
                if keyword in message:
                    return intent

        return "general"


class WechatService:
    """微信消息处理服务"""

    def __init__(self, db_session=None):
        self.db = db_session
        self.intent_detector = IntentDetector()

    async def handle_message(self, hotel_id: int, openid: str, message: str) -> dict:
        """处理微信消息"""
        intent = self.intent_detector.detect(message)
        response_text = self._generate_response(intent, message)

        result = {
            "intent": intent,
            "response": response_text,
        }

        from app.models import WechatMessage
        from app.services.crud_strategy import create_wechat_message
        from datetime import datetime

        if self.db:
            wechat_msg = WechatMessage(
                hotel_id=hotel_id,
                openid=openid,
                message=message,
                intent=intent,
                response=response_text,
                created_at=datetime.now(),
            )
            saved = create_wechat_message(self.db, wechat_msg)
            result["message_id"] = saved.id

        return result

    def _generate_response(self, intent: str, message: str) -> str:
        """根据意图生成简单回复"""
        responses = {
            "pricing": "正在为您分析今日定价策略，请稍候...",
            "room_status": "正在查询当前房态和竞品情况，请稍候...",
            "competitor": "正在获取竞品价格和房态数据，请稍候...",
            "report": "正在生成经营分析报告，请稍候...",
            "review_reply": "正在为您生成点评回复，请稍候...",
            "strategy": "正在为您制定经营策略，请稍候...",
            "greeting": "您好！我是您的 AI 酒店管家，请问有什么可以帮您？您可以问我定价、房态、竞品分析等问题。",
            "monthly_report": "正在生成本月经营报告，请稍候...",
            "general": "收到！让我帮您分析一下...",
        }
        return responses.get(intent, "收到！让我帮您处理...")
