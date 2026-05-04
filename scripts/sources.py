"""Конфигурация источников новостей и тем."""

RSS_FEEDS = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Wired AI", "url": "https://www.wired.com/feed/tag/ai/latest/rss"},
    {"name": "MIT Tech Review AI", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"},
]

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

# Ключевые слова для эвристической классификации (lowercase)
TOPIC_KEYWORDS = {
    "Models":      ["gpt", "claude", "llama", "gemini", "mistral", "model release", "fine-tune", "foundation model"],
    "Hardware":    ["gpu", "tpu", "nvidia", "h100", "h200", "blackwell", "chip", "accelerator", "asic"],
    "Regulations": ["regulation", "law", "act", "eu ai", "compliance", "policy", "ban", "executive order", "регулир", "закон"],
    "Startups":    ["startup", "seed", "series a", "series b", "raised", "funding", "valuation", "yc"],
    "Research":    ["paper", "benchmark", "arxiv", "research", "study", "dataset", "evaluation"],
    "AI Agents":   ["agent", "autonomous", "agentic", "tool use", "browser agent", "computer use"],
    "Corporate AI":["microsoft", "google", "meta", "amazon", "apple", "oracle", "enterprise", "earnings", "acquired"],
}
