"""Эвристическая классификация по темам на основе ключевых слов.

Читает data/latest.json, проставляет items[i]['topic'] и перезаписывает файл.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sources import TOPIC_KEYWORDS  # noqa: E402

DATA_PATH = ROOT / "data" / "latest.json"


def classify(text: str) -> str:
    t = text.lower()
    scores: dict[str, int] = {}
    for topic, kws in TOPIC_KEYWORDS.items():
        scores[topic] = sum(1 for kw in kws if kw in t)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Research"


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for item in payload["items"]:
        text = f"{item.get('title_en', '')} {item.get('summary_en', '')}"
        item["topic"] = classify(text)
    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[classify_news] classified {len(payload['items'])} items")


if __name__ == "__main__":
    main()
