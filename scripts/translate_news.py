"""Перевод заголовков и саммари на русский через OpenAI (gpt-4o-mini по умолчанию).

Использует cache/.translation-cache.json чтобы не переводить повторно.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "latest.json"
CACHE_PATH = ROOT / "cache" / ".translation-cache.json"

load_dotenv(ROOT / ".env")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "Ты переводчик технических AI-новостей с английского на русский. "
    "Сохраняй имена компаний, моделей и продуктов латиницей. "
    "Стиль — нейтральный, лаконичный, как у качественного русскоязычного техмедиа. "
    "Возвращай ТОЛЬКО перевод без преамбулы и без кавычек."
)


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def translate(client, text: str) -> str:
    if not text.strip():
        return ""
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        max_tokens=600,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[translate_news] OPENAI_API_KEY не задан — пропускаю перевод", file=sys.stderr)
        return

    try:
        from openai import OpenAI
    except ImportError:
        print("[translate_news] openai SDK не установлен", file=sys.stderr)
        return

    client = OpenAI(api_key=api_key)
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    cache = _load_cache()
    new_count = 0

    for item in payload["items"]:
        key_t = f"t::{item['id']}"
        key_s = f"s::{item['id']}"
        if key_t not in cache:
            cache[key_t] = translate(client, item.get("title_en", ""))
            new_count += 1
        if key_s not in cache:
            cache[key_s] = translate(client, item.get("summary_en", ""))
            new_count += 1
        item["title_ru"] = cache[key_t]
        item["summary_ru"] = cache[key_s]

    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _save_cache(cache)
    print(f"[translate_news] new translations: {new_count}, total cached: {len(cache)}")


if __name__ == "__main__":
    main()
