"""Сбор новостей за последние 24 часа из RSS + arXiv.

Сохраняет результат в data/latest.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sources import RSS_FEEDS, ARXIV_CATEGORIES  # noqa: E402

WINDOW_HOURS = 24
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
    for feed in RSS_FEEDS:
        parsed = feedparser.parse(feed["url"])
        for entry in parsed.entries:
            dt = _entry_dt(entry)
            if not dt or dt < cutoff:
                continue
            url = entry.get("link", "")
            if not url:
                continue
            items.append({
                "id": _stable_id(url),
                "source": feed["name"],
                "url": url,
                "title_en": entry.get("title", "").strip(),
                "summary_en": entry.get("summary", "").strip(),
                "published_at": dt.isoformat(),
            })
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
    for r in search.results():
        dt = r.published.astimezone(timezone.utc)
        if dt < cutoff:
            continue
        items.append({
            "id": _stable_id(r.entry_id),
            "source": "arXiv",
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

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "items": deduped}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[fetch_feeds] saved {len(deduped)} items → {DATA_PATH}")


if __name__ == "__main__":
    main()
