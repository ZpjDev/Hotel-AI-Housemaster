from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # 应用配置
    APP_NAME: str = "hotel-ai-butler"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-to-a-random-secret-key"

    # 数据库
    DATABASE_URL: str = "sqlite:///./hotel_ai_butler.db"

    # AI 配置 (OpenAI-compatible API)
    AI_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    AI_API_KEY: str = ""
    AI_MODEL: str = "qwen-turbo"

    # 微信配置
    WECHAT_TOKEN: str = ""
    WECHAT_ENCODING_AES_KEY: str = ""
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # OTA 数据 API
    OTA_API_BASE: str = ""
    OTA_API_KEY: str = ""

    # 电话 API
    PHONE_API_BASE: str = ""
    PHONE_API_KEY: str = ""

    # 通知配置
    NOTIFY_WEBHOOK_URL: str = ""

    # 定时任务
    SCHEDULER_ENABLED: bool = True


settings = Settings()
