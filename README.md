# AI Daily

Русскоязычный дашборд новостей искусственного интеллекта. Агрегирует RSS из ключевых источников, классифицирует материалы по темам, переводит заголовки и саммари на русский и формирует ежедневный digest.

Прод-версия: [ai-daily.pplx.app](https://ai-daily.pplx.app)

## Источники

- TechCrunch (AI секция)
- VentureBeat (AI)
- OpenAI Blog
- Hugging Face Blog
- Wired (AI)
- MIT Technology Review (AI)
- Google AI Blog
- arXiv (cs.AI, cs.LG, cs.CL)

## Темы

`Models` · `Hardware` · `Regulations` · `Startups` · `Research` · `AI Agents` · `Corporate AI`

## Структура проекта

```
ai-daily/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── data/
│   ├── latest.json          # последние новости за 24 часа
│   └── archive.json         # исторические данные
├── cache/
│   └── .translation-cache.json  # кэш переводов (OpenAI)
├── scripts/
│   ├── fetch_feeds.py       # сбор RSS + arXiv
│   ├── classify_news.py     # тематическая классификация
│   ├── translate_news.py    # перевод заголовков/саммари
│   └── build_digest.py      # сборка email-digest
├── site/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── .github/workflows/
    ├── update-news.yml      # cron 08:00 MSK — обновление ленты
    └── email-digest.yml     # cron 09:00 MSK — утренний digest
```

## Локальный запуск

```bash
git clone https://github.com/Cinderella789/ai-daily
cd ai-daily
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/fetch_feeds.py
python scripts/classify_news.py
python scripts/translate_news.py
python scripts/build_digest.py
```

Статический сайт открывается просто: `site/index.html`. Он читает `data/latest.json` и рендерит ленту с фильтрами по темам.

## Переменные окружения

Создай `.env` в корне (не коммитится):

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yuliacinderella789@gmail.com
SMTP_PASS=...
DIGEST_TO=yuliacinderella789@gmail.com
```

Для GitHub Actions те же значения нужно прописать в **Settings → Secrets and variables → Actions**.

## Расписание

| Workflow | Cron (UTC) | Что делает |
|---|---|---|
| `update-news.yml` | `0 5 * * *` (08:00 MSK) | Тянет RSS, классифицирует, переводит, коммитит обновлённый `data/latest.json` |
| `email-digest.yml` | `0 6 * * *` (09:00 MSK) | Собирает топ-5 за сутки и отправляет на `DIGEST_TO` |

## Деплой сайта

`Settings → Pages → Source: Deploy from a branch → main / site` или GitHub Actions с публикацией `site/`. Затем привязать кастомный домен `ai-daily.pplx.app` (CNAME на `cinderella789.github.io`).

## Лицензия

MIT — см. [LICENSE](LICENSE).
