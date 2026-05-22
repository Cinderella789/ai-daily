# infra/ — инфраструктурные скрипты для VPS

Эти скрипты крутятся на личном VPS Fornex (91.228.152.239) под пользователем `cinderella`
и запускаются через системный cron — см. crontab пользователя.

## Контекст

С 10.05.2026 cron-планировщик переехал с GitHub Actions на VPS:
GitHub Actions пропускал запуски и задерживал их на 4-5 часов
(см. `.github/workflows/update-news.yml` — там остался только `workflow_dispatch:`).

## Файлы

- `run-update.sh` — обновление RSS-ленты, каждые 4 часа (08, 12, 16, 20 MSK)
  - pipeline: `fetch_feeds → classify_news → translate_news → dedup_news → append_archive → mirror → commit & push`
  - Проверяет exit code `git push`, шлёт Telegram-алёрт при ошибке
  - Логи: `~/ai-daily/logs/update-YYYY-MM-DD_HH-MM.log` (хранятся 30 дней)

- `run-digest.sh` — утренняя email-рассылка дайджеста, 09:00 MSK
  - запускает `scripts/build_digest.py`, коммитит метку `data/.last-digest-date.txt`
  - те же проверки push exit + Telegram алёрты
  - Логи: `~/ai-daily/logs/digest-YYYY-MM-DD.log`

## Требуемые переменные окружения (в `~/ai-daily/.env`)

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
SMTP_HOST=...
SMTP_PORT=...
SMTP_USER=...
SMTP_PASS=...
DIGEST_TO=...
DIGEST_FROM_NAME=AI Daily
TZ=Europe/Moscow
TELEGRAM_BOT_TOKEN=...    # бот для алёртов о падениях cron
TELEGRAM_CHAT_ID=...      # личный chat_id для алёртов
```

## Деплой / обновление скриптов на VPS

```bash
# С локальной машины (Mac):
scp -P 49222 infra/run-update.sh cinderella@91.228.152.239:/home/cinderella/ai-daily/run-update.sh
scp -P 49222 infra/run-digest.sh cinderella@91.228.152.239:/home/cinderella/ai-daily/run-digest.sh
ssh -p 49222 cinderella@91.228.152.239 'chmod +x ~/ai-daily/run-update.sh ~/ai-daily/run-digest.sh'
```

## История инцидента 20-22.05.2026

`cache/.embeddings-cache.json` распух до 100+ МБ → push в GitHub блокировался
лимитом 100MB → 9 коммитов застряли локально → сайт не обновлялся 2 дня.

Починка:
1. `cache/` добавлен в `.gitignore`
2. `cache/*` убран из `git add` в `run-update.sh` и в `update-news.yml`
3. Добавлен exit code check у `git push` + Telegram-алёрт
4. Логирование вместо `> /dev/null 2>&1` в crontab
