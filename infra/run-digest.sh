#!/bin/bash
# Утренняя email-рассылка дайджеста ai-daily. Cron: 09:00 MSK (06:00 UTC).
# Восстановлен 22.05.2026 + добавлен push exit check + Telegram alert.

set -uo pipefail
cd ~/ai-daily

set -a
source .env
set +a

LOG_DIR=$HOME/ai-daily/logs
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/digest-$(date +%Y-%m-%d).log"

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
  echo "=== run-digest started: $(date -Iseconds)"

  .venv/bin/python scripts/build_digest.py || { send_alert "[ai-daily] build_digest FAILED"; exit 1; }

  .venv/bin/python scripts/send_telegram.py || { send_alert "[ai-daily] send_telegram FAILED"; echo "[tg] WARN: не отправлено, продолжаем"; }

  echo "--- commit & push ---"
  git config user.name "ai-daily-bot"
  git config user.email "ai-daily-bot@users.noreply.github.com"
  git add data/.last-digest-date.txt data/.last-tg-date.txt 2>/dev/null || true
  if git diff --cached --quiet; then
    echo "[commit] нечего коммитить (защёлка не изменилась)"
  else
    git commit -m "chore: digest sent $(date -u +%FT%TZ)"
    git push
    PUSH_EXIT=$?
    if [ $PUSH_EXIT -ne 0 ]; then
      MSG="<b>[ai-daily] DIGEST PUSH FAILED</b>%0A$(date -Iseconds)%0Aexit=$PUSH_EXIT"
      echo "[push] ОШИБКА (exit=$PUSH_EXIT)"
      send_alert "$MSG"
      exit $PUSH_EXIT
    else
      echo "[push] изменения отправлены ✓"
    fi
  fi

  echo "=== done: $(date -Iseconds)"
} 2>&1 | tee "$LOG"

find "$LOG_DIR" -name "digest-*.log" -mtime +30 -delete 2>/dev/null || true
