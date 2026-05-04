"""Конфигурация источников новостей и тем."""

RSS_FEEDS = [
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

# Источники, у которых контент уже на русском — перевод не нужен
RUSSIAN_SOURCES = {
    "Habr AI", "Habr ML", "Habr NLP", "Habr CV",
    "vc.ru AI", "vc.ru GPT",
}

ARXIV_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]

TOPICS = [
    "Models",
    "Hardware",
    "Regulations",
    "Startups",
    "Research",
    "AI Agents",
    "Corporate AI",
]

# Ключевые слова для эвристической классификации (lowercase, EN + RU)
TOPIC_KEYWORDS = {
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
