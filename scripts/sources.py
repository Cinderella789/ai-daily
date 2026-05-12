"""Конфигурация источников новостей и тем.

Каждый источник помечен категорией: "ai" или "crypto".
Категория попадает в каждую новость как поле item["category"].
"""

# ============================================================
# AI источники
# ============================================================
AI_RSS_FEEDS = [
    # Английские — индустрия
    {"name": "TechCrunch AI",    "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI",   "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "The Verge AI",     "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "Ars Technica AI",  "url": "https://arstechnica.com/ai/feed/"},
    {"name": "Wired AI",         "url": "https://www.wired.com/feed/tag/ai/latest/rss"},
    {"name": "MIT Tech Review",  "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "Platformer",       "url": "https://www.platformer.news/feed"},
    {"name": "Stratechery",      "url": "https://stratechery.com/feed/"},

    # Английские — лаборатории и компании
    {"name": "OpenAI Blog",      "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google AI Blog",   "url": "https://blog.google/technology/ai/rss/"},
    {"name": "Google Research",  "url": "https://research.google/blog/rss/"},
    {"name": "DeepMind Blog",    "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Hugging Face",     "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "NVIDIA AI Blog",   "url": "https://blogs.nvidia.com/feed/"},
    {"name": "NVIDIA Dev Blog",  "url": "https://developer.nvidia.com/blog/feed/"},

    # Английские — research / education
    {"name": "BAIR Blog",        "url": "https://bair.berkeley.edu/blog/feed.xml"},
    {"name": "Lil'Log",          "url": "https://lilianweng.github.io/index.xml"},
    {"name": "Sebastian Raschka","url": "https://magazine.sebastianraschka.com/feed"},
    {"name": "Simon Willison",   "url": "https://simonwillison.net/atom/everything/"},
    {"name": "Andrej Karpathy",  "url": "https://karpathy.github.io/feed.xml"},
    {"name": "AI Snake Oil",     "url": "https://www.aisnakeoil.com/feed"},
    {"name": "Last Week in AI",  "url": "https://lastweekin.ai/feed"},

    # Hacker News (только посты с 100+ голосами по AI/LLM)
    {"name": "Hacker News AI",   "url": "https://hnrss.org/newest?q=AI+OR+LLM&points=100"},

    # Русскоязычные
    {"name": "Habr AI",          "url": "https://habr.com/ru/rss/hub/artificial_intelligence/all/?fl=ru"},
    {"name": "Habr ML",          "url": "https://habr.com/ru/rss/hub/machine_learning/all/?fl=ru"},
    {"name": "Habr NLP",         "url": "https://habr.com/ru/rss/hub/natural_language_processing/all/?fl=ru"},
    {"name": "Habr CV",          "url": "https://habr.com/ru/rss/hub/image_processing/all/?fl=ru"},
    {"name": "vc.ru AI",         "url": "https://vc.ru/rss/tag/ai"},
    {"name": "vc.ru GPT",        "url": "https://vc.ru/rss/tag/gpt"},
]

# ============================================================
# Crypto источники
# ============================================================
CRYPTO_RSS_FEEDS = [
    # Английские — крупные медиа
    {"name": "CoinDesk",         "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "Cointelegraph",   "url": "https://cointelegraph.com/rss"},
    {"name": "The Block",       "url": "https://www.theblock.co/rss.xml"},
    {"name": "Decrypt",         "url": "https://decrypt.co/feed"},
    {"name": "CryptoSlate",     "url": "https://cryptoslate.com/feed/"},
    {"name": "Blockworks",      "url": "https://blockworks.co/feed"},
    {"name": "The Defiant",     "url": "https://thedefiant.io/feed"},
    {"name": "Crypto Briefing", "url": "https://cryptobriefing.com/feed/"},
    {"name": "Bitcoin.com",     "url": "https://news.bitcoin.com/feed/"},
    {"name": "Bitcoin Magazine","url": "https://bitcoinmagazine.com/.rss/full/"},
    {"name": "CryptoPotato",    "url": "https://cryptopotato.com/feed/"},
    {"name": "NewsBTC",         "url": "https://www.newsbtc.com/feed/"},
    {"name": "BeInCrypto EN",   "url": "https://beincrypto.com/feed/"},
    {"name": "Protos",          "url": "https://protos.com/feed/"},

    # Биржи и L1/L2
    {"name": "Ethereum Blog",   "url": "https://blog.ethereum.org/feed.xml"},
    {"name": "Solana Blog",     "url": "https://solana.com/news/rss.xml"},
    {"name": "Arbitrum Blog",   "url": "https://blog.arbitrum.io/rss/"},
    {"name": "Kraken Blog",     "url": "https://blog.kraken.com/feed/"},
    {"name": "Vitalik",         "url": "https://vitalik.eth.limo/feed.xml"},

    # Русскоязычные
    {"name": "Forklog",         "url": "https://forklog.com/feed"},
    {"name": "BeInCrypto RU",   "url": "https://ru.beincrypto.com/feed/"},
    {"name": "CoinSpot",        "url": "https://coinspot.io/feed/"},
    {"name": "InCrypted",       "url": "https://incrypted.com/feed/"},
    {"name": "HappyCoin",       "url": "https://happycoin.club/feed/"},
    {"name": "Habr Crypto",     "url": "https://habr.com/ru/rss/hub/cryptocurrency/all/?fl=ru"},
]

# Объединённый список (для обратной совместимости и общего fetch)
RSS_FEEDS = AI_RSS_FEEDS + CRYPTO_RSS_FEEDS

# Маппинг источник -> категория ("ai" или "crypto")
SOURCE_CATEGORY = {
    **{f["name"]: "ai"     for f in AI_RSS_FEEDS},
    **{f["name"]: "crypto" for f in CRYPTO_RSS_FEEDS},
    "arXiv": "ai",  # arXiv cs.AI/cs.LG/cs.CL
}

# Источники, у которых контент уже на русском — перевод не нужен
RUSSIAN_SOURCES = {
    "Habr AI", "Habr ML", "Habr NLP", "Habr CV",
    "vc.ru AI", "vc.ru GPT",
    "Forklog", "BeInCrypto RU", "CoinSpot", "InCrypted", "HappyCoin",
    "Habr Crypto",
}

ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]

# Темы для AI-новостей
TOPICS_AI = [
    "Models",
    "Hardware",
    "Regulations",
    "Startups",
    "Research",
    "AI Agents",
    "Corporate AI",
]

# Темы для Crypto-новостей
TOPICS_CRYPTO = [
    "Bitcoin",
    "Ethereum",
    "DeFi",
    "Altcoins",
    "Regulations",
    "Hacks",
    "Macro",
    "NFT & Gaming",
]

# Объединённый список (для обратной совместимости)
TOPICS = TOPICS_AI + TOPICS_CRYPTO

# Ключевые слова для эвристической классификации (lowercase, EN + RU)
TOPIC_KEYWORDS_AI = {
    "Models": [
        "gpt", "claude", "llama", "gemini", "mistral", "qwen", "deepseek",
        "model release", "fine-tune", "foundation model", "новая модель",
        "релиз модели", "языковая модель", "llm",
    ],
    "Hardware": [
        "gpu", "tpu", "nvidia", "h100", "h200", "blackwell", "chip",
        "accelerator", "asic", "процессор", "ускоритель", "видеокарта",
        "чип", "железо",
    ],
    "Regulations": [
        "regulation", "law", "act", "eu ai", "compliance", "policy", "ban",
        "executive order", "регулир", "закон", "запрет", "штраф",
        "требования", "минцифры", "указ",
    ],
    "Startups": [
        "startup", "seed", "series a", "series b", "raised", "funding",
        "valuation", "yc", "стартап", "раунд", "инвестиции", "оценка",
        "привлекли", "поднял",
    ],
    "Research": [
        "paper", "benchmark", "arxiv", "research", "study", "dataset",
        "evaluation", "статья", "исследование", "бенчмарк", "датасет",
    ],
    "AI Agents": [
        "agent", "autonomous", "agentic", "tool use", "browser agent",
        "computer use", "агент", "автономн", "агентн",
    ],
    "Corporate AI": [
        "microsoft", "google", "meta", "amazon", "apple", "oracle",
        "enterprise", "earnings", "acquired", "яндекс", "сбер",
        "тинькофф", "т-банк", "вк", "корпорат",
    ],
}

TOPIC_KEYWORDS_CRYPTO = {
    "Bitcoin": [
        "bitcoin", " btc ", "btc/", "satoshi", "halving", "lightning network",
        "биткоин", "биткойн", "халвинг", "сатоши",
    ],
    "Ethereum": [
        "ethereum", " eth ", "eth/", "vitalik", "layer 2", "l2", "rollup",
        "optimism", "arbitrum", "base", "zksync", "starknet",
        "эфир", "эфириум", "виталик", "роллап",
    ],
    "DeFi": [
        "defi", "uniswap", "aave", "curve", "maker", "compound", "lido",
        "liquidity", "yield", "farming", "staking", "lending", "perp",
        "perpetual", "dex", "amm", "tvl", "vault",
        "дефи", "децентрализован", "ликвидност", "стейкинг", "фарм",
    ],
    "Altcoins": [
        "solana", " sol ", "avalanche", " avax", "cardano", " ada ",
        "polkadot", " dot ", "chainlink", " link ", "polygon", "matic",
        "sui", "aptos", "near", "cosmos", "atom",
        "meme", "memecoin", "мем-коин", "альткоин", "альт",
        "doge", "shib", "pepe", "bonk", "wif",
    ],
    "Regulations": [
        "sec", "cftc", "regulation", "compliance", "lawsuit", "ban",
        "approved", "approval", "settlement", "licence", "license",
        "mica", "кик", "цб", "центробанк", "закон", "регулирован",
        "запрет", "одобрил", "иск", "штраф", "лицензи",
    ],
    "Hacks": [
        "hack", "exploit", "drained", "stolen", "breach", "vulnerability",
        "rug pull", "phishing", "attack", "compromised",
        "взлом", "эксплойт", "украл", "уязвимост", "скам", "скам-проект",
        "взломали", "вывели",
    ],
    "Macro": [
        "etf", "futures", "fed", "federal reserve", "interest rate",
        "inflation", "institutional", "blackrock", "fidelity", "grayscale",
        "microstrategy", "strategy", "michael saylor",
        "фрс", "ставк", "инфляц", "институционал", "фьючерс", "этф",  # этф = ETF
    ],
    "NFT & Gaming": [
        "nft", "opensea", "blur", "magic eden", "gamefi", "play-to-earn",
        "p2e", "axie", "sandbox", "decentraland",
        "нфт", "геймфай", "плэй-ту-эрн", "геймин",
    ],
}

# Объединённый словарь — используется classify_news.py если нужна общая классификация
TOPIC_KEYWORDS = {**TOPIC_KEYWORDS_AI, **TOPIC_KEYWORDS_CRYPTO}
