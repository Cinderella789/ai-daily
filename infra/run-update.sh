#!/bin/bash
# Обновление RSS-ленты ai-daily. Cron каждые 4 часа (08, 12, 16, 20 MSK).
# Восстановлен 22.05.2026 после потери оригинала + добавлен push exit check + Telegram alert.

set -uo pipefail
cd ~/ai-daily

# Загружаем .env (OPENAI_API_KEY, OPENAI_MODEL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TZ)
set -a
source .env
set +a

LOG_DIR=$HOME/ai-daily/logs
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/update-$(date +%Y-%m-%d_%H-%M).log"

# Хелпер для Telegram-алёрта
send_alert() {
  local MSG="$1"
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ "$TELEGRAM_BOT_TOKEN" != "PLACEHOLDER_TODO_FILL" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
      -d chat_id="$TELEGRAM_CHAT_ID" \
      -d text="$MSG" \
      -d parse_mode="HTML" >/dev/null 2>&1 || true
  fi
}

{
  echo "=== run-update started: $(date -Iseconds)"

  echo "--- git pull ---"
  if ! git pull --rebase origin main; then
    echo "[ERROR] git pull упал"
    send_alert "<b>[ai-daily] git pull FAILED</b>%0A$(date -Iseconds)"
    exit 1
  fi

  echo "--- fetch ---"
  .venv/bin/python scripts/fetch_feeds.py || { send_alert "[ai-daily] fetch_feeds FAILED"; exit 1; }

  echo "--- classify ---"
  .venv/bin/python scripts/classify_news.py || { send_alert "[ai-daily] classify_news FAILED"; exit 1; }

  echo "--- translate ---"
  .venv/bin/python scripts/translate_news.py || { send_alert "[ai-daily] translate_news FAILED"; exit 1; }

  echo "--- dedup ---"
  .venv/bin/python scripts/dedup_news.py || { send_alert "[ai-daily] dedup_news FAILED"; exit 1; }

  echo "--- archive ---"
  .venv/bin/python scripts/append_archive.py || { send_alert "[ai-daily] append_archive FAILED"; exit 1; }

  echo "--- mirror ---"
  mkdir -p site/data
  cp data/latest.json site/data/latest.json
  cp data/archive.json site/data/archive.json

  echo "--- commit & push ---"
  git config user.name "ai-daily-bot"
  git config user.email "ai-daily-bot@users.noreply.github.com"
  # ВНИМАНИЕ: cache/* НЕ добавляем — там может вырасти > 100MB blob
  git add data/latest.json site/data/latest.json data/archive.json site/data/archive.json
  if git diff --cached --quiet; then
    echo "[commit] нечего коммитить"
  else
    git commit -m "chore: refresh news $(date -u +%FT%TZ)"
    git push
    PUSH_EXIT=$?
    if [ $PUSH_EXIT -ne 0 ]; then
      MSG="<b>[ai-daily] PUSH FAILED</b>%0A$(date -Iseconds)%0Aexit=$PUSH_EXIT%0Aлог: $LOG"
      echo "[push] ОШИБКА (exit=$PUSH_EXIT)"
      send_alert "$MSG"
      exit $PUSH_EXIT
    else
      echo "[push] изменения отправлены ✓"
    fi
  fi

  echo "--- telegram ---"
  .venv/bin/python scripts/send_telegram.py || { send_alert "[ai-daily] send_telegram FAILED"; echo "[tg] WARN: не отправлено, продолжаем"; }

  echo "=== done: $(date -Iseconds)"
} 2>&1 | tee "$LOG"

# Чистим логи старше 30 дней
find "$LOG_DIR" -name "update-*.log" -mtime +30 -delete 2>/dev/null || true
