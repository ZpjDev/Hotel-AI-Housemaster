from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlmodel import Session
from app.database import get_session
from app.services.ai_provider import AIProvider
from app.services.strategy_service import StrategyService
from app.services.external_api.ota_data_service import OTADataService
from app.services.report_service import ReportService
from app.services.wechat.wechat_service import WechatService
from app.services.wechat.wechat_provider import get_wechat_provider
from app.models import Hotel
from datetime import datetime
from sqlmodel import select
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
async def wechat_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    """微信公众号/企业微信 Webhook"""
    from xml.etree import ElementTree

    body = await request.body()
    xml_data = body.decode("utf-8")

    try:
        root = ElementTree.fromstring(xml_data)
        to_user = root.findtext("ToUserName", "")
        from_user = root.findtext("FromUserName", "")
        msg_type = root.findtext("MsgType", "text")
        content = root.findtext("Content", "")
    except Exception:
        logger.error(f"微信消息解析失败: {xml_data[:100]}")
        return PlainTextResponse("success")

    openid = from_user
    message = content

    hotel = session.exec(select(Hotel).where(Hotel.boss_openid == openid)).first()
    if not hotel:
        logger.warning(f"未找到 openid {openid} 绑定的酒店")
        return PlainTextResponse("success")

    wechat_provider = get_wechat_provider()
    wechat_svc = WechatService(session)
    ai = AIProvider()
    ota = OTADataService(session)
    strategy_svc = StrategyService(session, ai, ota)

    message_result = await wechat_svc.handle_message(
        hotel_id=hotel.id,
        openid=openid,
        message=message,
    )

    reply_text = message_result["response"]

    if message_result["intent"] in ["pricing", "room_status", "competitor", "strategy"]:
        try:
            strategy_result = await strategy_svc.generate_strategy(
                hotel_id=hotel.id,
                question=message,
            )
            reply_text = strategy_result["full_report"]
        except Exception as e:
            reply_text += f"\n\n策略生成失败: {str(e)}"
    elif message_result["intent"] == "monthly_report":
        report_svc = ReportService(session, ai)
        month = datetime.now().strftime("%Y-%m")
        reply_text = await report_svc.generate_monthly_report(hotel.id, month)
    elif message_result["intent"] in ["greeting", "general"]:
        try:
            prompt = f"你是一个专业的酒店经营AI管家，服务于{hotel.name}。酒店位于{hotel.city}，有{hotel.total_rooms}间房。用户说：{message}。请给出专业、有帮助的回复（不超过200字）。"
            reply_text = await ai.chat_completion([{"role": "user", "content": prompt}])
        except Exception:
            reply_text = f"您好！{message}"

    logger.info(f"[微信] {openid} ({hotel.name}): {message[:50]}...")

    response_xml = f"""<xml>
<ToUserName><![CDATA[{openid}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(datetime.now().timestamp())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{reply_text}]]></Content>
</xml>"""

    return PlainTextResponse(content=response_xml, media_type="application/xml")


@router.get("/webhook")
async def wechat_webhook_verify(
    signature: str = "",
    timestamp: str = "",
    nonce: str = "",
    echostr: str = "",
):
    """微信公众号 Token 校验"""
    provider = get_wechat_provider()
    token = getattr(provider, "token", "")
    if not token:
        return PlainTextResponse(echostr)

    if provider.verify_signature(timestamp, nonce, signature):
        return PlainTextResponse(echostr)
    return PlainTextResponse("fail")
