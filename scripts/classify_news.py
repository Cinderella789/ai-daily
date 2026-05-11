"""Эвристическая классификация по темам на основе ключевых слов.

Читает data/latest.json, проставляет items[i]['topic'] и перезаписывает файл.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sources import TOPIC_KEYWORDS_AI, TOPIC_KEYWORDS_CRYPTO  # noqa: E402

DATA_PATH = ROOT / "data" / "latest.json"


def classify(text: str, category: str) -> str:
    """Классифицирует новость по теме внутри своей категории.

    AI новости могут иметь темы: Models, Hardware, ...
    Crypto новости могут иметь темы: Bitcoin, Ethereum, DeFi, ...
    """
    keywords = TOPIC_KEYWORDS_CRYPTO if category == "crypto" else TOPIC_KEYWORDS_AI
    fallback = "Altcoins" if category == "crypto" else "Research"

    t = text.lower()
    scores: dict[str, int] = {}
    for topic, kws in keywords.items():
        scores[topic] = sum(1 for kw in kws if kw in t)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else fallback


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for item in payload["items"]:
        text = f"{item.get('title_en', '')} {item.get('summary_en', '')}"
        category = item.get("category", "ai")
        item["topic"] = classify(text, category)
    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[classify_news] classified {len(payload['items'])} items")


if __name__ == "__main__":
    main()
