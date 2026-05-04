"""Дописывает свежие новости из data/latest.json в data/archive.json.

Хранит до ARCHIVE_MAX_ITEMS последних материалов (по дате публикации).
Дубликаты отбрасываются по полю id.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LATEST_PATH = ROOT / "data" / "latest.json"
ARCHIVE_PATH = ROOT / "data" / "archive.json"
SITE_ARCHIVE_PATH = ROOT / "site" / "data" / "archive.json"

ARCHIVE_MAX_ITEMS = 5000  # ~год при ~15/день


def main() -> None:
    latest = json.loads(LATEST_PATH.read_text(encoding="utf-8"))
    new_items = latest.get("items", [])

    if ARCHIVE_PATH.exists():
        archive = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
    else:
        archive = {"items": []}

    existing_ids = {it["id"] for it in archive["items"]}
    added = [it for it in new_items if it["id"] not in existing_ids]

    archive["items"].extend(added)
    archive["items"].sort(key=lambda x: x.get("published_at", ""), reverse=True)
    archive["items"] = archive["items"][:ARCHIVE_MAX_ITEMS]
    archive["updated_at"] = datetime.now(timezone.utc).isoformat()
    archive["total"] = len(archive["items"])

    payload = json.dumps(archive, ensure_ascii=False, indent=2)
    ARCHIVE_PATH.write_text(payload, encoding="utf-8")
    SITE_ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SITE_ARCHIVE_PATH.write_text(payload, encoding="utf-8")

    print(f"[append_archive] +{len(added)} new, total {len(archive['items'])}")


if __name__ == "__main__":
    main()
