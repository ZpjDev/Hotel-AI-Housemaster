"""Configure WeChat API settings in the local APIConfig table."""
from getpass import getpass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import Session

from app.database import create_db_and_tables, engine
from app.models import APIConfig
from app.services.crud_others import create_api_config


def prompt_value(label: str, secret: bool = False, default: str = "") -> str:
    prompt = f"{label}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    value = getpass(prompt) if secret else input(prompt)
    return value.strip() or default


def upsert_config(session: Session, key: str, value: str, is_encrypted: bool, description: str) -> None:
    create_api_config(
        session,
        APIConfig(
            key=key,
            value=value,
            is_encrypted=is_encrypted,
            description=description,
        ),
    )


def main() -> None:
    print("WeChat API configuration")
    print("Leave EncodingAESKey empty if your WeChat server uses plaintext mode.")
    app_id = prompt_value("WECHAT_APP_ID / AppID")
    app_secret = prompt_value("WECHAT_APP_SECRET / AppSecret", secret=True)
    token = prompt_value("WECHAT_TOKEN / server Token", secret=True)
    encoding_aes_key = prompt_value("WECHAT_ENCODING_AES_KEY / EncodingAESKey", secret=True)

    create_db_and_tables()
    with Session(engine) as session:
        upsert_config(session, "wechat_app_id", app_id, False, "微信公众号/企业微信 AppID")
        upsert_config(session, "wechat_app_secret", app_secret, True, "微信公众号/企业微信 AppSecret")
        upsert_config(session, "wechat_token", token, True, "微信公众号/企业微信 Webhook Token")
        upsert_config(
            session,
            "wechat_encoding_aes_key",
            encoding_aes_key,
            True,
            "微信消息加解密 EncodingAESKey（明文模式可留空）",
        )

    print("WeChat API settings saved.")
    print("Configure this callback URL in WeChat:")
    print("  https://YOUR_PUBLIC_DOMAIN/wechat/webhook")


if __name__ == "__main__":
    main()
