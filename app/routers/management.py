from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from sqlmodel import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_session
from app.models import Customer, Review, OTAOrder, PendingAction, APIConfig, KnowledgeBase
from app.schemas import (
    CustomerCreate, CustomerResponse,
    ReviewCreate, ReviewResponse,
    OTAOrderCreate, OTAOrderResponse,
    PendingActionCreate, PendingActionResponse,
    APIConfigCreate, APIConfigUpdate, APIConfigResponse,
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
)
from app.services.crud_others import (
    create_customer, get_customers, get_customer,
    create_review, get_reviews, update_review_reply,
    create_ota_order, get_ota_orders,
    create_pending_action, get_pending_actions, update_pending_action,
    create_api_config, get_api_config, get_api_configs, update_api_config,
)
from app.services.ai_provider import decrypt_value

router = APIRouter()


def mask_value(value: str) -> str:
    """脱敏 API Key"""
    if not value:
        return "****"
    if len(value) <= 8:
        return "****" + value[-4:]
    return value[:4] + "****" + value[-4:]


def safe_mask_value(raw_value: str, is_encrypted: bool, encrypted_value: str = None) -> str:
    """安全脱敏：先解密再脱敏，不返回真实值"""
    if not raw_value:
        return None
    return mask_value(raw_value)


def _build_api_config_response(config) -> dict:
    """构建 APIConfig 响应，加密值先解密再脱敏，永不返回真实 value"""
    if config.is_encrypted:
        if config.value:
            raw = decrypt_value(config.value)
            masked = mask_value(raw) if raw else None
        else:
            masked = None
        return {
            "id": config.id, "key": config.key, "value": "",
            "masked_value": masked,
            "description": config.description, "is_encrypted": config.is_encrypted,
            "created_at": config.created_at, "updated_at": config.updated_at,
        }
    else:
        return {
            "id": config.id, "key": config.key, "value": config.value or "",
            "masked_value": None,
            "description": config.description, "is_encrypted": config.is_encrypted,
            "created_at": config.created_at, "updated_at": config.updated_at,
        }


class PhoneMockCallRequest(BaseModel):
    hotel_id: int
    phone: str
    transcript: str


class CustomerQuestionRequest(BaseModel):
    hotel_id: int
    question: str


# ============ 客户 ============
@router.post("/customers", response_model=CustomerResponse)
def api_create_customer(data: CustomerCreate, session: Session = Depends(get_session)):
    customer = Customer(**data.model_dump())
    return create_customer(session, customer)


@router.get("/hotels/{hotel_id}/customers", response_model=List[CustomerResponse])
def api_get_customers(hotel_id: int, session: Session = Depends(get_session)):
    return get_customers(session, hotel_id)


# ============ 点评 ============
@router.post("/reviews", response_model=ReviewResponse)
def api_create_review(data: ReviewCreate, session: Session = Depends(get_session)):
    review = Review(**data.model_dump())
    return create_review(session, review)


@router.get("/hotels/{hotel_id}/reviews", response_model=List[ReviewResponse])
def api_get_reviews(hotel_id: int, session: Session = Depends(get_session)):
    return get_reviews(session, hotel_id)


# ============ 订单 ============
@router.post("/orders", response_model=OTAOrderResponse)
def api_create_order(data: OTAOrderCreate, session: Session = Depends(get_session)):
    order = OTAOrder(**data.model_dump())
    return create_ota_order(session, order)


@router.get("/hotels/{hotel_id}/orders", response_model=List[OTAOrderResponse])
def api_get_orders(hotel_id: int, session: Session = Depends(get_session)):
    return get_ota_orders(session, hotel_id)


@router.put("/orders/{order_id}", response_model=OTAOrderResponse)
def api_update_order(order_id: int, data: dict, session: Session = Depends(get_session)):
    from sqlmodel import select
    order = session.get(OTAOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if "status" in data:
        order.status = data["status"]
    from datetime import datetime
    order.updated_at = datetime.now()
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


# ============ 待确认动作 ============
@router.post("/pending-actions", response_model=PendingActionResponse)
def api_create_pending_action(data: PendingActionCreate, session: Session = Depends(get_session)):
    action = PendingAction(**data.model_dump())
    return create_pending_action(session, action)


@router.get("/hotels/{hotel_id}/pending-actions", response_model=List[PendingActionResponse])
def api_get_pending_actions(hotel_id: int, session: Session = Depends(get_session)):
    return get_pending_actions(session, hotel_id)


@router.put("/pending-actions/{action_id}", response_model=PendingActionResponse)
def api_update_pending_action(
    action_id: int,
    status: str = Form(...),
    session: Session = Depends(get_session),
):
    action = update_pending_action(session, action_id, status)
    if not action:
        raise HTTPException(status_code=404, detail="动作不存在")
    return action


# ============ API 配置 ============
@router.post("/api-configs", response_model=APIConfigResponse)
def api_create_api_config(data: APIConfigCreate, session: Session = Depends(get_session)):
    config = APIConfig(**data.model_dump())
    created = create_api_config(session, config)
    return APIConfigResponse(**_build_api_config_response(created))


@router.get("/api-configs", response_model=List[APIConfigResponse])
def api_get_api_configs(session: Session = Depends(get_session)):
    configs = get_api_configs(session)
    return [APIConfigResponse(**_build_api_config_response(c)) for c in configs]


@router.put("/api-configs/{key}", response_model=APIConfigResponse)
def api_update_api_config(
    key: str, data: APIConfigUpdate, session: Session = Depends(get_session),
):
    config = update_api_config(session, key, data.value)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return APIConfigResponse(**_build_api_config_response(config))


# ============ 知识库 ============
@router.get("/hotels/{hotel_id}/knowledge-base", response_model=KnowledgeBaseResponse)
def api_get_knowledge_base(hotel_id: int, session: Session = Depends(get_session)):
    from sqlmodel import select
    kb = session.exec(select(KnowledgeBase).where(KnowledgeBase.hotel_id == hotel_id)).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


@router.put("/hotels/{hotel_id}/knowledge-base", response_model=KnowledgeBaseResponse)
def api_update_knowledge_base(
    hotel_id: int, data: KnowledgeBaseUpdate, session: Session = Depends(get_session),
):
    from sqlmodel import select
    kb = session.exec(select(KnowledgeBase).where(KnowledgeBase.hotel_id == hotel_id)).first()
    if kb:
        for key, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(kb, key, value)
        from datetime import datetime
        kb.updated_at = datetime.now()
        session.add(kb)
        session.commit()
        session.refresh(kb)
    else:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


@router.post("/hotels/{hotel_id}/knowledge-base", response_model=KnowledgeBaseResponse)
def api_create_knowledge_base(
    hotel_id: int, data: KnowledgeBaseCreate, session: Session = Depends(get_session),
):
    kb = KnowledgeBase(**data.model_dump())
    session.add(kb)
    session.commit()
    session.refresh(kb)
    return kb


# ============ 电话模拟接口 ============
@router.post("/phone/mock-inbound-call")
async def api_mock_inbound_call(
    request: Request,
    hotel_id: Optional[int] = None,
    phone: Optional[str] = None,
    transcript: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """模拟来电（测试用），优先读取知识库
    支持两种调用方式：
    1. Query 参数: POST /api/phone/mock-inbound-call?hotel_id=1&phone=xxx&transcript=xxx
    2. JSON Body: {"hotel_id": 1, "phone": "13800000000", "transcript": "请问你们可以停车吗？"}
    """
    try:
        body = await request.json()
        hotel_id = body.get("hotel_id", hotel_id)
        phone = body.get("phone", phone)
        transcript = body.get("transcript", transcript)
    except Exception:
        pass

    if not hotel_id or not transcript:
        raise HTTPException(status_code=400, detail="缺少 hotel_id 或 transcript 参数")

    from sqlmodel import select
    from app.services.ai_provider import AIProvider
    import logging
    logger = logging.getLogger(__name__)

    kb = session.exec(select(KnowledgeBase).where(KnowledgeBase.hotel_id == hotel_id)).first()
    kb_context = ""
    if kb:
        kb_context = f"""
【酒店知识库】
- 酒店名称：{kb.hotel_name}
- 地址：{kb.address}
- 电话：{kb.phone}
- 入住时间：{kb.checkin_time}
- 退房时间：{kb.checkout_time}
- 停车：{kb.parking_info}
- 早餐：{kb.breakfast_info}
- 宠物：{kb.pet_policy}
- 发票：{kb.invoice_policy}
- 取消政策：{kb.cancellation_policy}
- 交通：{kb.nearby_transport}
- 景点：{kb.nearby_attractions}
- WiFi：{kb.wifi_info}
"""

    ai = AIProvider()
    prompt = f"""客户来电：{transcript}

{kb_context}

请根据以上知识库信息回答客户问题。
要求：
1. 优先使用知识库内容回答
2. 不知道的信息不能胡编，请提示联系前台确认
3. 回答简洁友好，不超过 100 字
"""

    try:
        answer = await ai.chat_completion([
            {"role": "system", "content": "你是一位酒店客服，负责接听客户电话并回答问题。"},
            {"role": "user", "content": prompt},
        ])
        need_human = "转人工" in answer or "人工服务" in answer
    except Exception:
        if kb:
            answer = f"您好！关于您的问题，我们的信息是：{kb.parking_info or kb.breakfast_info or '请联系前台获取详细信息'}。如需更多帮助，请致电前台：{kb.phone}。"
        else:
            answer = "您好！请稍等，我为您转接前台。"
        need_human = False

    return {"status": "ok", "answer": answer, "need_human": need_human}


# ============ 客户问题回复 ============
@router.post("/ai/customer-question-reply")
async def api_customer_question_reply(
    request: Request,
    hotel_id: Optional[int] = None,
    question: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """客户问题自动回复，优先读取知识库
    支持两种调用方式：
    1. Query 参数: POST /api/ai/customer-question-reply?hotel_id=1&question=xxx
    2. JSON Body: {"hotel_id": 1, "question": "你们能开发票吗？可以停车吗？"}
    """
    try:
        body = await request.json()
        hotel_id = body.get("hotel_id", hotel_id)
        question = body.get("question", question)
    except Exception:
        pass

    if not hotel_id or not question:
        raise HTTPException(status_code=400, detail="缺少 hotel_id 或 question 参数")

    from sqlmodel import select
    from app.services.ai_provider import AIProvider

    kb = session.exec(select(KnowledgeBase).where(KnowledgeBase.hotel_id == hotel_id)).first()
    kb_context = ""
    if kb:
        kb_context = f"""
【酒店知识库】
- 酒店名称：{kb.hotel_name}
- 地址：{kb.address}
- 电话：{kb.phone}
- 入住时间：{kb.checkin_time}
- 退房时间：{kb.checkout_time}
- 停车：{kb.parking_info}
- 早餐：{kb.breakfast_info}
- 宠物：{kb.pet_policy}
- 发票：{kb.invoice_policy}
- 取消政策：{kb.cancellation_policy}
- 交通：{kb.nearby_transport}
- 景点：{kb.nearby_attractions}
- WiFi：{kb.wifi_info}
"""

    ai = AIProvider()
    prompt = f"""客户问题：{question}

{kb_context}

请根据以上知识库信息回答客户问题。
要求：
1. 优先使用知识库内容回答
2. 不知道的信息不能胡编，请提示联系前台确认
3. 不确定时请提示联系前台
4. 回答友好专业，不超过 100 字
"""

    try:
        reply = await ai.chat_completion([
            {"role": "system", "content": "你是一位酒店客服，负责回答客户问题。"},
            {"role": "user", "content": prompt},
        ])
    except Exception:
        if kb:
            reply = f"您好！感谢您的咨询。{kb.wifi_info or '如需更多信息，请联系前台：' + kb.phone}"
        else:
            reply = "您好！感谢您的咨询。如需详细信息，请联系前台。"

    return {"reply": reply}
