from app.models import Customer, Review, OTAOrder, PendingAction, APIConfig, APILog
from sqlmodel import Session, select
from typing import Optional, List
from app.services.ai_provider import encrypt_value, decrypt_value


DEFAULT_API_CONFIGS = [
    ("ai_api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1", False, "AI OpenAI-compatible API Base URL"),
    ("ai_api_key", "", True, "AI API Key"),
    ("ai_model", "qwen-turbo", False, "AI 模型名称"),
    ("wechat_token", "", True, "微信公众号/企业微信 Webhook Token"),
    ("wechat_encoding_aes_key", "", True, "微信消息加解密 EncodingAESKey（明文模式可留空）"),
    ("wechat_app_id", "", False, "微信公众号/企业微信 AppID"),
    ("wechat_app_secret", "", True, "微信公众号/企业微信 AppSecret"),
    ("ota_api_base", "", False, "OTA 数据 API Base URL"),
    ("ota_api_key", "", True, "OTA 数据 API Key"),
    ("phone_api_base", "", False, "电话服务 API Base URL"),
    ("phone_api_key", "", True, "电话服务 API Key"),
    ("notify_webhook_url", "", True, "通知 Webhook URL"),
]


def create_customer(session: Session, customer: Customer) -> Customer:
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def get_customers(session: Session, hotel_id: int) -> List[Customer]:
    statement = select(Customer).where(Customer.hotel_id == hotel_id)
    return list(session.exec(statement).all())


def get_customer(session: Session, customer_id: int) -> Optional[Customer]:
    return session.get(Customer, customer_id)


def create_review(session: Session, review: Review) -> Review:
    session.add(review)
    session.commit()
    session.refresh(review)
    return review


def get_reviews(session: Session, hotel_id: int) -> List[Review]:
    statement = select(Review).where(Review.hotel_id == hotel_id).order_by(Review.created_at.desc())
    return list(session.exec(statement).all())


def update_review_reply(session: Session, review_id: int, reply_content: str) -> Optional[Review]:
    review = session.get(Review, review_id)
    if not review:
        return None
    review.reply_content = reply_content
    review.reply_status = "replied"
    from datetime import datetime
    review.updated_at = datetime.now()
    session.add(review)
    session.commit()
    session.refresh(review)
    return review


def create_ota_order(session: Session, order: OTAOrder) -> OTAOrder:
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def get_ota_orders(session: Session, hotel_id: int) -> List[OTAOrder]:
    statement = select(OTAOrder).where(OTAOrder.hotel_id == hotel_id).order_by(OTAOrder.created_at.desc())
    return list(session.exec(statement).all())


def create_pending_action(session: Session, action: PendingAction) -> PendingAction:
    session.add(action)
    session.commit()
    session.refresh(action)
    return action


VALID_PENDING_STATUSES = {"pending", "approved", "rejected", "executed", "failed"}


def get_pending_actions(session: Session, hotel_id: int = None, status: str = None) -> List[PendingAction]:
    statement = select(PendingAction)
    conditions = []
    if hotel_id is not None:
        conditions.append(PendingAction.hotel_id == hotel_id)
    if status:
        conditions.append(PendingAction.status == status)
    else:
        conditions.append(PendingAction.status == "pending")
    for cond in conditions:
        statement = statement.where(cond)
    statement = statement.order_by(PendingAction.created_at.desc())
    return list(session.exec(statement).all())


def update_pending_action(
    session: Session, action_id: int, status: str, failed_reason: str = None
) -> Optional[PendingAction]:
    if status not in VALID_PENDING_STATUSES:
        raise ValueError(f"无效状态: {status}，允许的状态: {VALID_PENDING_STATUSES}")

    action = session.get(PendingAction, action_id)
    if not action:
        return None
    from datetime import datetime
    action.status = status
    if status == "approved":
        action.approved_at = datetime.now()
    elif status == "executed":
        action.executed_at = datetime.now()
    elif status == "failed":
        if failed_reason:
            action.failed_reason = failed_reason
    session.add(action)
    session.commit()
    session.refresh(action)
    return action


def create_api_config(session: Session, config: APIConfig) -> APIConfig:
    existing = get_api_config(session, config.key)
    if existing:
        return update_api_config(session, config.key, decrypt_value(config.value) if config.is_encrypted else config.value)
    if config.is_encrypted and config.value and not config.value.startswith("enc:"):
        config.value = encrypt_value(config.value)
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def get_api_config(session: Session, key: str) -> Optional[APIConfig]:
    statement = select(APIConfig).where(APIConfig.key == key)
    return session.exec(statement).first()


def get_api_configs(session: Session) -> List[APIConfig]:
    ensure_default_api_configs(session)
    return list(session.exec(select(APIConfig)).all())


def ensure_default_api_configs(session: Session) -> None:
    changed = False
    for key, value, is_encrypted, description in DEFAULT_API_CONFIGS:
        if get_api_config(session, key):
            continue
        config = APIConfig(
            key=key,
            value=encrypt_value(value) if is_encrypted and value else value,
            is_encrypted=is_encrypted,
            description=description,
        )
        session.add(config)
        changed = True
    if changed:
        session.commit()


def update_api_config(session: Session, key: str, value: str) -> Optional[APIConfig]:
    statement = select(APIConfig).where(APIConfig.key == key)
    config = session.exec(statement).first()
    if not config:
        return None
    if value is not None:
        if config.is_encrypted and value:
            config.value = encrypt_value(value) if not value.startswith("enc:") else value
        else:
            config.value = value
    from datetime import datetime
    config.updated_at = datetime.now()
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


def create_api_log(session: Session, log: APILog) -> APILog:
    session.add(log)
    session.commit()
    session.refresh(log)
    return log
