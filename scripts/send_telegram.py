"""Отправка топ-5 дайджеста в Telegram-канал."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "latest.json"
LOCK_PATH = ROOT / "data" / ".last-tg-date.txt"

load_dotenv(ROOT / ".env")

_MONTHS = ["янв", "фев", "мар", "апр", "мая", "июн",
           "июл", "авг", "сен", "окт", "ноя", "дек"]
_NUM_EMOJI = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
_TOPIC_EMOJI = {
    # AI
    "Models": "🤖", "Research": "🔬", "AI Agents": "🕵️", "Hardware": "🖥️",
    "Startups": "🚀", "Regulations": "📜", "Corporate AI": "🏢",
    # Crypto
    "Bitcoin": "₿", "Ethereum": "⟠", "Altcoins": "🪙",
    "DeFi": "💸", "Macro": "📈", "Hacks": "🔓", "NFT & Gaming": "🎮",
}


_COOLDOWN_HOURS = 3  # минимум между отправками


def _sent_recently() -> bool:
    if not LOCK_PATH.exists():
        return False
    try:
        last = datetime.fromisoformat(LOCK_PATH.read_text(encoding="utf-8").strip())
        return (datetime.now(timezone.utc) - last).total_seconds() < _COOLDOWN_HOURS * 3600
    except Exception:
        return False


def _mark_sent() -> None:
    LOCK_PATH.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _diverse(pool: list[dict], n: int) -> list[dict]:
    by_topic: dict[str, list[dict]] = {}
    for it in pool:
        by_topic.setdefault(it.get("topic", "Other"), []).append(it)
    result: list[dict] = []
    while len(result) < n and any(by_topic.values()):
        for lst in list(by_topic.values()):
            if not lst:
                continue
            result.append(lst.pop(0))
            if len(result) >= n:
                break
    return result


def pick_top(items: list[dict], n_ai: int = 3, n_crypto: int = 2) -> list[dict]:
    ai = [it for it in items if it.get("category") == "ai"]
    crypto = [it for it in items if it.get("category") == "crypto"]
    return _diverse(ai, n_ai) + _diverse(crypto, n_crypto)


def render(items: list[dict]) -> str:
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    date_str = f"{now.day} {_MONTHS[now.month - 1]}"
    time_str = now.strftime("%H:%M")

    parts = [f"🗞 <b>AI Daily · {date_str} · {time_str} МСК</b>"]

    for i, it in enumerate(items):
        title = _esc(it.get("title_ru") or it.get("title_en", ""))
        summary = it.get("summary_ru") or it.get("summary_en", "")
        if len(summary) > 300:
            summary = summary[:297] + "…"
        summary = _esc(summary)
        topic = it.get("topic", "")
        source = it.get("source", "")
        url = it.get("url", "")
        num = _NUM_EMOJI[i] if i < 5 else f"{i + 1}."
        emoji = _TOPIC_EMOJI.get(topic, "📰")

        parts.append(
            f"{num} {emoji} <b><a href=\"{url}\">{title}</a></b>\n"
            f"<i>{_esc(topic)} · {_esc(source)}</i>\n"
            f"{summary}"
        )

    parts.append("🔗 <a href=\"https://ai-daily-9au.pages.dev\">Полная лента</a>")
    return "\n\n".join(parts)


def send(text: str) -> None:
    token = os.environ["TELEGRAM_DIGEST_BOT_TOKEN"]
    channel = os.environ["TELEGRAM_CHANNEL_ID"]
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": channel,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    resp.raise_for_status()
    print(f"[send_telegram] OK — message_id={resp.json()['result']['message_id']}")


def main() -> None:
    force = "--force" in sys.argv
    if not force and _sent_recently():
        print(f"[send_telegram] последняя отправка была менее {_COOLDOWN_HOURS}ч назад — пропускаю")
        return

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    top = pick_top(payload["items"])
    if not top:
        print("[send_telegram] нет новостей — пропускаю")
        return

    text = render(top)

    if "--dry-run" in sys.argv or not os.environ.get("TELEGRAM_DIGEST_BOT_TOKEN"):
        print("[send_telegram] dry-run:")
        print(text)
        return

    send(text)
    _mark_sent()
    print(f"[send_telegram] отправлено {len(top)} новостей")


if __name__ == "__main__":
    main()
