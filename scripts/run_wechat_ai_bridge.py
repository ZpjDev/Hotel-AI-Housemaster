"""Run the local WeChat <-> AI bridge with a few operator-friendly checks."""
import argparse
import asyncio
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
from app.models import Hotel
from app.services.ai_provider import AIProvider, get_wechat_config
from app.services.wechat.wechat_provider import OfficialWechatProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run WeChat AI bridge")
    parser.add_argument("--host", default="0.0.0.0", help="Uvicorn host")
    parser.add_argument("--port", type=int, default=8000, help="Uvicorn port")
    parser.add_argument(
        "--public-base-url",
        default="",
        help="Public HTTPS base URL that WeChat can reach, e.g. https://bot.example.com",
    )
    parser.add_argument("--hotel-id", type=int, default=0, help="Hotel ID for the optional self-test")
    parser.add_argument("--openid", default="", help="OpenID for the optional self-test message")
    parser.add_argument(
        "--question",
        default="请给我一条测试消息，确认微信 AI 管家已经接通。",
        help="Question used for the optional self-test message",
    )
    parser.add_argument(
        "--skip-self-test",
        action="store_true",
        help="Only start the webhook server, skip the outbound AI test message",
    )
    return parser.parse_args()


def validate_config() -> tuple[OfficialWechatProvider, AIProvider]:
    wechat_config = get_wechat_config()
    missing = [
        key for key in ("app_id", "app_secret", "token")
        if not wechat_config.get(key)
    ]
    if missing:
        missing_text = ", ".join(missing)
        raise SystemExit(
            f"WeChat config is incomplete. Missing: {missing_text}. "
            "Fill api_configs first with scripts/wechat_one_click_setup.py or scripts/configure_wechat.py."
        )

    provider = OfficialWechatProvider()
    ai_provider = AIProvider()
    return provider, ai_provider


def get_hotel(hotel_id: int) -> Hotel | None:
    if not hotel_id:
        return None
    with Session(engine) as session:
        return session.exec(select(Hotel).where(Hotel.id == hotel_id)).first()


async def run_self_test(provider: OfficialWechatProvider, ai_provider: AIProvider, hotel: Hotel, openid: str, question: str) -> None:
    answer = await ai_provider.chat_completion([
        {"role": "system", "content": "你是酒店 AI 管家，请用简洁自然的中文回复测试消息。"},
        {"role": "user", "content": question},
    ])
    message = f"【{hotel.name} AI 管家测试】\n{answer}"
    result = await provider.send_message(openid, message)
    errcode = result.get("errcode", 0)
    if errcode not in (0, "0"):
        raise SystemExit(f"WeChat self-test failed: {result}")
    print("WeChat self-test message sent successfully.")


def print_runtime_summary(args: argparse.Namespace, hotel: Hotel | None) -> None:
    callback_url = ""
    if args.public_base_url:
        callback_url = args.public_base_url.rstrip("/") + "/wechat/webhook"

    print("WeChat AI bridge is starting.")
    print(f"Local webhook:  http://{args.host}:{args.port}/wechat/webhook")
    if callback_url:
        print(f"Public webhook: {callback_url}")
        print("Use this in WeChat MP server configuration.")
    else:
        print("Public webhook: <not set>")
        print("Pass --public-base-url https://your-domain to print the final callback URL.")

    if hotel:
        print(f"Hotel mapping:   {hotel.id} -> {hotel.name} / boss_openid={hotel.boss_openid}")


def start_server(args: argparse.Namespace) -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault("SCHEDULER_ENABLED", "false")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ],
        env=env,
    )


def wait_for_server(args: argparse.Namespace, timeout_seconds: float = 15.0) -> None:
    import httpx

    deadline = time.time() + timeout_seconds
    health_url = f"http://127.0.0.1:{args.port}/health"
    last_error = "unknown"
    while time.time() < deadline:
        try:
            response = httpx.get(health_url, timeout=2.0)
            if response.status_code == 200:
                return
            last_error = f"status={response.status_code}"
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.5)
    raise SystemExit(f"Webhook server did not become ready in time: {last_error}")


def main() -> None:
    args = parse_args()
    create_db_and_tables()

    provider, ai_provider = validate_config()
    hotel = get_hotel(args.hotel_id)
    if args.hotel_id and not hotel:
        raise SystemExit(f"Hotel {args.hotel_id} was not found.")

    if not args.skip_self_test:
        if not hotel or not args.openid:
            raise SystemExit("Self-test requires both --hotel-id and --openid, or use --skip-self-test.")
        asyncio.run(run_self_test(provider, ai_provider, hotel, args.openid, args.question))

    print_runtime_summary(args, hotel)
    server = start_server(args)
    try:
        wait_for_server(args)
        print("Webhook server is ready.")
        print("Press Ctrl+C to stop the bridge.")
        server.wait()
    except KeyboardInterrupt:
        server.terminate()
    finally:
        if server.poll() is None:
            server.terminate()


if __name__ == "__main__":
    main()
