"""Семантическая дедупликация новостей.

Использует OpenAI embeddings (text-embedding-3-small) для поиска дублей —
случаев, когда несколько источников пишут об одном событии.

Алгоритм:
1. Загружаем data/latest.json
2. Считаем embedding для каждого заголовка (title_en + первые 200 симв. summary_en)
3. Кластеризуем по cosine similarity > THRESHOLD
4. В каждом кластере оставляем самую раннюю новость (первоисточник),
   остальные складываем в поле `duplicates` как [{source, url, title_en}]
5. Сохраняем обратно в data/latest.json

Результаты embeddings кэшируются по id в cache/.embeddings-cache.json.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "latest.json"
CACHE_PATH = ROOT / "cache" / ".embeddings-cache.json"

SIMILARITY_THRESHOLD = 0.82
EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def _embed_text(item: dict) -> str:
    title = item.get("title_en") or item.get("title_ru") or ""
    summary = (item.get("summary_en") or item.get("summary_ru") or "")[:200]
    return f"{title}. {summary}".strip()


def get_embeddings(items: list[dict], cache: dict) -> dict[str, list[float]]:
    """Возвращает {id: embedding}, использует кэш и батч-запрос для новых."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[dedup] OPENAI_API_KEY не задан — пропускаю дедупликацию", file=sys.stderr)
        return {}

    try:
        from openai import OpenAI
    except ImportError:
        print("[dedup] openai SDK не установлен — пропускаю", file=sys.stderr)
        return {}

    client = OpenAI(api_key=api_key)

    result: dict[str, list[float]] = {}
    to_fetch: list[tuple[str, str]] = []  # [(id, text)]

    for it in items:
        iid = it["id"]
        if iid in cache:
            result[iid] = cache[iid]
        else:
            text = _embed_text(it)
            if text:
                to_fetch.append((iid, text))

    # Батч-запрос (OpenAI поддерживает массив input)
    if to_fetch:
        BATCH = 100
        for i in range(0, len(to_fetch), BATCH):
            chunk = to_fetch[i : i + BATCH]
            try:
                resp = client.embeddings.create(
                    model=EMBED_MODEL,
                    input=[t for _, t in chunk],
                )
                for (iid, _), data in zip(chunk, resp.data):
                    result[iid] = data.embedding
                    cache[iid] = data.embedding
            except Exception as e:
                print(f"[dedup] ошибка embeddings: {e}", file=sys.stderr)

    return result


def cluster(items: list[dict], embeds: dict[str, list[float]]) -> list[list[int]]:
    """Жадная кластеризация. Возвращает список кластеров (списков индексов)."""
    n = len(items)
    cluster_of = [-1] * n
    clusters: list[list[int]] = []

    for i in range(n):
        if cluster_of[i] != -1:
            continue
        emb_i = embeds.get(items[i]["id"])
        if not emb_i:
            cluster_of[i] = len(clusters)
            clusters.append([i])
            continue
        # Создаём новый кластер
        cid = len(clusters)
        cluster_of[i] = cid
        members = [i]
        for j in range(i + 1, n):
            if cluster_of[j] != -1:
                continue
            emb_j = embeds.get(items[j]["id"])
            if not emb_j:
                continue
            if _cosine(emb_i, emb_j) >= SIMILARITY_THRESHOLD:
                cluster_of[j] = cid
                members.append(j)
        clusters.append(members)

    return clusters


def main() -> None:
    if not DATA_PATH.exists():
        print(f"[dedup] {DATA_PATH} не найден — пропускаю")
        return

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    items: list[dict] = payload.get("items", [])
    if len(items) < 2:
        print("[dedup] меньше 2 новостей — нечего дедуплицировать")
        return

    cache = _load_cache()
    embeds = get_embeddings(items, cache)
    _save_cache(cache)

    if not embeds:
        return

    clusters = cluster(items, embeds)

    deduped: list[dict] = []
    merged_count = 0
    for members in clusters:
        if len(members) == 1:
            deduped.append(items[members[0]])
            continue
        # Сортируем по published_at — оставляем самую раннюю как первоисточник
        members_sorted = sorted(members, key=lambda k: items[k].get("published_at", ""))
        primary = dict(items[members_sorted[0]])
        duplicates = []
        for idx in members_sorted[1:]:
            d = items[idx]
            duplicates.append({
                "source": d.get("source"),
                "url": d.get("url"),
                "title_en": d.get("title_en"),
                "title_ru": d.get("title_ru"),
                "published_at": d.get("published_at"),
            })
            merged_count += 1
        primary["duplicates"] = duplicates
        deduped.append(primary)

    deduped.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    payload["items"] = deduped
    payload["dedup_at"] = datetime.utcnow().isoformat() + "Z"

    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"[dedup] было {len(items)}, кластеров {len(clusters)}, "
        f"объединено {merged_count} дублей → итого {len(deduped)}"
    )


if __name__ == "__main__":
    main()
