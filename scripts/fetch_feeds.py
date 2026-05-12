"""Сбор новостей за последние 24 часа из RSS + arXiv.

Сохраняет результат в data/latest.json.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Рекламные / промо-маркеры. Проверяются в URL и заголовке (lower).
_PROMO_PATTERNS = [
    # TechCrunch и другие венчурные издания пихают рекламу своих конференций
    "disrupt", "early-bird", "early bird", "last-chance", "last chance",
    "days-left", "days left", "hours-left", "hours left",
    "% off", "discount", "promo", "sponsored", "webinar",
    "register-now", "register now", "limited-time", "limited time",
    "осталось", "скидк", "промокод", "купите билет", "билеты на",
]


def _is_promo(title: str, url: str) -> bool:
    haystack = f"{title} {url}".lower()
    return any(p in haystack for p in _PROMO_PATTERNS)


def _clean_html(text: str) -> str:
    """Убираем HTML-теги и лишние пробелы."""
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sources import RSS_FEEDS, ARXIV_CATEGORIES, SOURCE_CATEGORY  # noqa: E402

WINDOW_HOURS = 24
MAX_PER_SOURCE = 8  # ограничение выдачи одного источника — чтобы лента была разнообразной
MAX_PER_CATEGORY = 80  # ограничение на категорию (ai/crypto), чтобы одна не забивала другую
DATA_PATH = ROOT / "data" / "latest.json"


def _stable_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def _entry_dt(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        val = getattr(entry, key, None) or entry.get(key)
        if val:
            return datetime(*val[:6], tzinfo=timezone.utc)
    return None


def fetch_rss() -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=WINDOW_HOURS)
    items: list[dict] = []
    failed: list[str] = []
    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
        except Exception as e:
            failed.append(f"{feed['name']}: {type(e).__name__}")
            continue
        if getattr(parsed, "bozo", 0) and not getattr(parsed, "entries", None):
            failed.append(f"{feed['name']}: parse failed")
            continue
        for entry in parsed.entries:
            dt = _entry_dt(entry)
            if not dt or dt < cutoff:
                continue
            url = entry.get("link", "")
            if not url:
                continue
            title = _clean_html(entry.get("title", ""))
            if _is_promo(title, url):
                continue
            items.append({
                "id": _stable_id(url),
                "source": feed["name"],
                "category": SOURCE_CATEGORY.get(feed["name"], "ai"),
                "url": url,
                "title_en": title,
                "summary_en": _clean_html(entry.get("summary", "")),
                "published_at": dt.isoformat(),
            })
    if failed:
        print(f"[fetch_rss] skipped {len(failed)} failing feeds: {failed[:5]}")
    return items


def fetch_arxiv() -> list[dict]:
    try:
        import arxiv  # type: ignore
    except ImportError:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=WINDOW_HOURS)
    items: list[dict] = []
    query = " OR ".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
    search = arxiv.Search(
        query=query,
        max_results=50,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    try:
        results = list(search.results())
    except Exception as e:
        print(f"[fetch_arxiv] skipped due to API error: {type(e).__name__}: {e}")
        return []
    for r in results:
        dt = r.published.astimezone(timezone.utc)
        if dt < cutoff:
            continue
        items.append({
            "id": _stable_id(r.entry_id),
            "source": "arXiv",
            "category": "ai",
            "url": r.entry_id,
            "title_en": r.title.strip(),
            "summary_en": r.summary.strip(),
            "published_at": dt.isoformat(),
        })
    return items


def main() -> None:
    all_items = fetch_rss() + fetch_arxiv()
    # Дедупликация по id
    seen, deduped = set(), []
    for it in all_items:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        deduped.append(it)
    deduped.sort(key=lambda x: x["published_at"], reverse=True)

    # Ограничиваем количество материалов от одного источника и от категории
    src_counts: dict[str, int] = {}
    cat_counts: dict[str, int] = {}
    capped: list[dict] = []
    for it in deduped:
        src = it["source"]
        cat = it.get("category", "ai")
        if src_counts.get(src, 0) >= MAX_PER_SOURCE:
            continue
        if cat_counts.get(cat, 0) >= MAX_PER_CATEGORY:
            continue
        src_counts[src] = src_counts.get(src, 0) + 1
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        capped.append(it)
    deduped = capped

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "items": deduped}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[fetch_feeds] saved {len(deduped)} items → {DATA_PATH}")


if __name__ == "__main__":
    main()
