"""One-click local setup helper for WeChat integration.

This script keeps secrets on the local machine:
- writes WeChat settings to the APIConfig table with existing encryption logic
- opens the WeChat MP console and local admin pages
- optionally starts the FastAPI service
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import webbrowser
from getpass import getpass

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import Session

from app.database import create_db_and_tables, engine
from app.models import APIConfig
from app.services.crud_others import create_api_config


WECHAT_MP_HOME = "https://mp.weixin.qq.com/"
LOCAL_ADMIN_API_SETTINGS = "http://localhost:8000/admin/api-settings"


def prompt(label: str, secret: bool = False, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = getpass(f"{label}{suffix}: ") if secret else input(f"{label}{suffix}: ")
    return value.strip() or default


def save_config(key: str, value: str, encrypted: bool, description: str) -> None:
    with Session(engine) as session:
        create_api_config(
            session,
            APIConfig(
                key=key,
                value=value,
                is_encrypted=encrypted,
                description=description,
            ),
        )


def configure_wechat() -> tuple[str, str]:
    print("\nStep 1/3: WeChat settings")
    print("Find these in WeChat MP: 设置与开发 -> 基本配置.")
    app_id = prompt("AppID / wechat_app_id")
    app_secret = prompt("AppSecret / wechat_app_secret", secret=True)
    token = prompt("Server Token / wechat_token", secret=True)
    encoding_aes_key = prompt("EncodingAESKey / wechat_encoding_aes_key (empty for plaintext)", secret=True)
    public_base_url = prompt("Public HTTPS base URL, e.g. https://example.com")
    callback_url = public_base_url.rstrip("/") + "/wechat/webhook"

    create_db_and_tables()
    save_config("wechat_app_id", app_id, False, "微信公众号/企业微信 AppID")
    save_config("wechat_app_secret", app_secret, True, "微信公众号/企业微信 AppSecret")
    save_config("wechat_token", token, True, "微信公众号/企业微信 Webhook Token")
    save_config("wechat_encoding_aes_key", encoding_aes_key, True, "微信消息加解密 EncodingAESKey（明文模式可留空）")

    print("\nSaved local WeChat settings.")
    print("\nStep 2/3: Put this in WeChat MP server configuration")
    print(f"URL: {callback_url}")
    print("Token: the Server Token you just entered")
    print("EncodingAESKey: the EncodingAESKey you just entered, or leave plaintext mode if empty")
    print("Message encryption mode: plaintext first, then switch later if needed")
    return callback_url, public_base_url


def open_pages() -> None:
    print("\nOpening WeChat MP and local API settings pages...")
    webbrowser.open(WECHAT_MP_HOME)
    webbrowser.open(LOCAL_ADMIN_API_SETTINGS)


def start_server() -> subprocess.Popen:
    print("\nStep 3/3: Starting FastAPI on http://localhost:8000")
    env = os.environ.copy()
    env.setdefault("SCHEDULER_ENABLED", "false")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        env=env,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="One-click WeChat integration setup")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser pages")
    parser.add_argument("--no-server", action="store_true", help="Do not start FastAPI")
    args = parser.parse_args()

    configure_wechat()

    server = None
    if not args.no_server:
        server = start_server()

    if not args.no_browser:
        open_pages()

    if server:
        print("\nServer is running. Press Ctrl+C to stop it.")
        try:
            server.wait()
        except KeyboardInterrupt:
            server.terminate()


if __name__ == "__main__":
    main()
