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


# Крипто-релевантные маркеры. Если новость идёт из crypto-источника, но
# в её заголовке/URL нет НИ ОДНОГО из этих слов — значит это оффтоп
# (политика, спорт, общие новости с РБК-подобных лент) и её надо отбросить.
_CRYPTO_MARKERS = [
    # EN
    "crypto", "bitcoin", "btc", "ethereum", "eth", "defi", "nft", "web3",
    "blockchain", "token", "stablecoin", "solana", "sol ", "xrp",
    "binance", "coinbase", "kraken", "okx", "bybit", "bitfinex",
    "altcoin", "sec ", "etf", "halving", "satoshi", "vitalik",
    "layer 2", "l2", "rollup", "arbitrum", "optimism", "polygon", "base",
    "airdrop", "staking", "validator", "hodl", "dao", "dex", "cex",
    "memecoin", "meme coin", "shitcoin", "miner", "mining", "hashrate",
    "wallet", "hyperliquid", "chainlink", "avalanche", "cardano", "ada ",
    "polkadot", "cosmos", "sui ", "aptos", "near ", "dogecoin", "doge",
    "pepe", "shib", "wif", "bonk", "uniswap", "aave", "curve", "maker",
    "compound", "lido", "tron", "trx", "litecoin", "ltc", "monero", "xmr",
    "hack", "exploit", "rug", "phishing",
    # RU
    "крипт", "биткоин", "биткойн", "эфир", "эфириум", "альткоин",
    "блокчейн", "токен", "стейблкоин", "майнинг", "майнер", "халвинг",
    "виталик", "сатоши", "кошел", "стейкинг", "эирдроп", "эйрдроп",
    "мем-коин", "мемкоин", "децентрализован", "смарт-контракт",
    "бинанс", "коинбейс", "бирж", "децентрализованн", "defi",
]


# WordPress-лента дописывает в summary "The post <title> appeared first on <Site>".
# Имя сайта (Crypto Briefing, CryptoSlate…) содержит крипто-маркер → любой оффтоп
# ложно проходит фильтр. Вырезаем этот хвост перед проверкой релевантности.
_WP_BOILERPLATE_RE = re.compile(r"the post\b.*?appeared first on.*", re.I)

# Поиск маркеров с границей слова слева (\b), чтобы "defi" не ловил "redefine",
# "base" — "database", "maker" — "filmmaker". Префиксы (крипт, майнинг) при этом
# работают: \b стоит перед маркером, а конец остаётся открытым. Хвостовые пробелы
# в самих маркерах ("sec ", "eth ") сохраняют границу справа.
_MARKER_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(m) for m in _CRYPTO_MARKERS) + r")",
    re.IGNORECASE,
)

# Источники, которые подмешивают в крипто-ленту общий оффтоп (спорт, политику,
# знаменитостей) с ЕДИНСТВЕННЫМ случайным упоминанием крипты — напр. "Bitcoin
# rallies" в новости про США/Иран или "and crypto" в заметке про Роналду.
# Для них требуем больше сигнала: не один маркер, а >=2 РАЗНЫХ. У остальных
# (CoinDesk, Bitcoin Magazine и пр.) оставляем мягкое правило — иначе режутся
# нормальные одно-монетные заголовки (XRP, UNI, OM, SBF-кейсы и т.п.).
_NOISY_CRYPTO_SOURCES = ("crypto briefing",)


def _is_crypto_relevant(title: str, summary: str, source_name: str = "") -> bool:
    """True если новость про крипту.

    Базово: в ЗАГОЛОВКЕ или ОПИСАНИИ есть хотя бы один крипто-маркер. URL НЕ
    учитываем (домен крипто-сайтов содержит маркеры и пропускал любой оффтоп).
    Имя источника вырезаем (оно может содержать маркер). Для «шумных» источников
    (_NOISY_CRYPTO_SOURCES) порог выше — >=2 разных маркера, чтобы отсеять
    статьи про спорт/политику с одиночным упоминанием крипты.
    """
    clean_summary = _WP_BOILERPLATE_RE.sub(" ", summary)
    title_l = title.lower()
    summary_l = clean_summary.lower()
    if source_name:
        src = source_name.lower()
        title_l = title_l.replace(src, " ")
        summary_l = summary_l.replace(src, " ")
    haystack = f"{title_l} {summary_l}"
    matches = _MARKER_RE.findall(haystack)
    if not matches:
        return False
    if any(n in source_name.lower() for n in _NOISY_CRYPTO_SOURCES):
        # Шумный источник: его summary авто-генерится с крипто-уклоном даже для
        # спорта/политики («...fan token market... for crypto investors» в
        # новости про футбол), поэтому тему честно отражает только ЗАГОЛОВОК.
        # Требуем маркер в заголовке + >=2 РАЗНЫХ маркера суммарно.
        if not _MARKER_RE.search(title_l):
            return False
        return len({m.lower() for m in matches}) >= 2
    return True


# ── Жёсткий отсев НЕ-технологического контента ──────────────────────────────
# Канал про технологии: убираем политику, рынки/цены/макро и спорт ПОЛНОСТЬЮ,
# в обеих категориях (ai/crypto), даже если упомянута крипта/ИИ. Ловим по
# ЗАГОЛОВКУ (там тема статьи; summary бывает с искусственным крипто-уклоном).

_POLITICS_RE = re.compile(r"""(?ix)\b(
  trump|biden|putin|zelensky\w*|netanyahu|kim\ jong|xi\ jinping|maga|
  white\ house|kremlin|senate|senators?|congress\w*|lawmakers?|parliament|
  primaries|presidential|elections?|governor|politburo|geopolit\w*|
  peace\ deal|ceasefire|world\ leaders|strait\ of\ hormuz|airstrikes?|
  missile|troops|diplomat\w*|treaty|tariffs?|nuclear\ deal|sanctions\ on|
  asylum|deport\w*|immigration|g7|g20|united\ nations|
  трамп|байден|путин|зеленск\w*|нетаньяху|белый\ дом|кремл\w*|сенат|
  конгресс|парламент|депутат|госдум\w*|выбор[ыа]|президент\w*|экс-премьер\w*|
  премьер-министр\w*|геополит\w*|перемири\w*|войн[аеуы]|санкции\ против|
  убежищ\w*|мигрант\w*|саммит\w*|оон
)\b""")

_MARKETS_RE = re.compile(r"""(?ix)(
  \bprice\ (analysis|prediction|target)|\brall(y|ies|ied)\b|\bplunge\w*|
  \bsurge\w*|\bsoars?\b|\bsoaring\b|\btumbl\w*|\bslump\w*|\bplummet\w*|
  \bsell-?off\b|\bcrash\w*|\bdump\w*|\bpump\w*|\bbullish\b|\bbearish\b|
  \ball-?time\ high\b|\bath\b|\bliquidat\w*|\bshorts?\b|\blongs?\b|
  \beyes\ \$|\btargets?\ \$|\bhits\ \$|\bholds\ (above|below)|\$\d|
  \bmarket\ cap\b|\bsupport\ level|\bresistance\b|\bforecast\w*|
  \boutperform\w*|\d+\s*%|\bfomc\b|\bfed\b|\brate\ cut|\binflation\b|
  \binterest\ rate|\btreasury\ yield|\boil\ price|\bstock\ market|
  \bnasdaq\b|\bs&p\b|\bdow\ jones|\brecession\b|\bopen\ interest\b|
  \bmoving\ average|\d+-?(week|day)\ (average|moving)|dollar\ index|
  \bbreakout\b|after\ the\ fed|fed\ decision|wall\ street|
  цен[аыу]|ралли|обвал\w*|рухнул\w*|взлет\w*|подорожал\w*|подешевел\w*|
  рост\ цен|прогноз\ цен|ликвидаци\w*|открыт\w*\ интерес|индекс\ доллара|
  \d+-?недельн\w*|скользящ\w*\ средн|прорыв\w*|после\ решения\ фрс|уолл-стрит|
  лонг\w*|шорт\w*|рыно?к|рыночн\w*|инфляци\w*|ставк[аеу]\ (цб|фрс)|решени\w*\ фрс
)""")

_SPORTS_RE = re.compile(r"""(?ix)\b(
  football|soccer|world\ cup|premier\ league|champions\ league|la\ liga|
  ronaldo|messi|grealish|outfield|goalkeeper|striker|midfielder|
  nba|nfl|mlb|nhl|olympics?|tennis|golf|athlete|transfer\ window|
  injury\ layoff|on\ the\ pitch|world\ series|grand\ slam|
  футбол\w*|спорт\w*|чемпионат|роналду|месси|матч|лиг[аеи]\ чемпион
)\b""")


def _offtopic_reason(title: str) -> str | None:
    """Возвращает причину отсева НЕ-тех контента или None. Канал про технологии:
    политика/рынки/спорт вырезаются полностью в обеих категориях."""
    t = title or ""
    if _POLITICS_RE.search(t):
        return "politics"
    if _SPORTS_RE.search(t):
        return "sports"
    if _MARKETS_RE.search(t):
        return "markets"
    return None


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
            summary = _clean_html(entry.get("summary", ""))
            category = SOURCE_CATEGORY.get(feed["name"], "ai")
            # Защита от оффтопа в крипто-категории (политика, спорт и пр.
            # подмешиваются с общих RU-лент вроде РБК)
            if category == "crypto" and not _is_crypto_relevant(title, summary, feed["name"]):
                continue
            # Канал про технологии: жёстко выкидываем политику/рынки/спорт
            # в ОБЕИХ категориях (даже если упомянута крипта/ИИ).
            off = _offtopic_reason(title)
            if off:
                continue
            items.append({
                "id": _stable_id(url),
                "source": feed["name"],
                "category": category,
                "url": url,
                "title_en": title,
                "summary_en": summary,
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
