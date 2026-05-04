"""Сборка и отправка утреннего email-digest (топ-5 новостей за сутки)."""
from __future__ import annotations

import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "latest.json"

load_dotenv(ROOT / ".env")


def pick_top(items: list[dict], n: int = 5) -> list[dict]:
    # Приоритизируем разнообразие тем + свежесть
    by_topic: dict[str, list[dict]] = {}
    for it in items:
        by_topic.setdefault(it.get("topic", "Research"), []).append(it)
    top: list[dict] = []
    while len(top) < n and any(by_topic.values()):
        for topic, lst in list(by_topic.items()):
            if not lst:
                continue
            top.append(lst.pop(0))
            if len(top) >= n:
                break
    return top


def render_html(items: list[dict]) -> str:
    rows = []
    for it in items:
        title = it.get("title_ru") or it.get("title_en", "")
        summary = it.get("summary_ru") or it.get("summary_en", "")
        rows.append(f"""
        <div style="margin:0 0 24px 0;padding:0 0 16px 0;border-bottom:1px solid #eee;">
          <div style="font-size:12px;color:#888;text-transform:uppercase;letter-spacing:.05em;">
            {it.get('topic', '')} · {it.get('source', '')}
          </div>
          <a href="{it['url']}" style="font-size:18px;font-weight:600;color:#111;text-decoration:none;">
            {title}
          </a>
          <p style="font-size:14px;color:#444;line-height:1.5;margin:8px 0 0 0;">{summary[:400]}</p>
        </div>
        """)
    return f"""
    <html><body style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:0 auto;padding:24px;">
      <h1 style="font-size:22px;margin:0 0 24px 0;">AI Daily — утренний дайджест</h1>
      {''.join(rows)}
      <p style="font-size:12px;color:#aaa;">Полная лента: <a href="https://ai-daily-9au.pages.dev">ai-daily-9au.pages.dev</a></p>
    </body></html>
    """


def _parse_recipients(raw: str) -> list[str]:
    """Разбирает 'a@b.com, c@d.com; e@f.com' в список адресов."""
    parts: list[str] = []
    for chunk in raw.replace(";", ",").split(","):
        addr = chunk.strip()
        if addr:
            parts.append(addr)
    return parts


def send(html: str, subject: str) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    pwd = os.environ["SMTP_PASS"]
    recipients = _parse_recipients(os.environ["DIGEST_TO"])
    from_name = os.environ.get("DIGEST_FROM_NAME", "AI Daily")

    if not recipients:
        raise RuntimeError("DIGEST_TO пустой — некому слать")

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, pwd)
        # Отправляем каждому отдельным письмом — адреса не видны друг другу
        for to in recipients:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{user}>"
            msg["To"] = to
            msg.attach(MIMEText(html, "html", "utf-8"))
            s.sendmail(user, [to], msg.as_string())
            print(f"[build_digest] → {to}")


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    top = pick_top(payload["items"], n=5)
    if not top:
        print("[build_digest] нет новостей за сутки — digest не отправлен")
        return
    html = render_html(top)
    if "--dry-run" in sys.argv or not os.environ.get("SMTP_HOST"):
        out = ROOT / "data" / "digest_preview.html"
        out.write_text(html, encoding="utf-8")
        print(f"[build_digest] dry-run → {out}")
        return
    from datetime import datetime
    months = ["янв", "фев", "мар", "апр", "мая", "июн",
              "июл", "авг", "сен", "окт", "ноя", "дек"]
    today = datetime.now()
    date_str = f"{today.day} {months[today.month - 1]}"
    subject = f"AI Daily · {date_str} · топ-5 новостей"
    send(html, subject=subject)
    print(f"[build_digest] отправлено {len(top)} новостей")


if __name__ == "__main__":
    main()
