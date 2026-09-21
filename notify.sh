#!/bin/bash
# Универсальный отправщик Telegram-уведомлений
# Использование: ./notify.sh "<severity>" "<message>"
#   severity: info | warn | critical
set +e

SEVERITY="${1:-info}"
MESSAGE="${2:-no message}"

# Токен и чат — из .env (21.09): репозиторий публичный, в коде их держать нельзя.
[ -f "$HOME/ai-daily/.env" ] && . "$HOME/ai-daily/.env"
TG_TOKEN="${NOTIFY_BOT_TOKEN:-}"
TG_CHAT_ID="${NOTIFY_CHAT_ID:-}"
if [ -z "$TG_TOKEN" ] || [ -z "$TG_CHAT_ID" ]; then
  # Молча не выходим: без этого алерты исчезли бы незаметно — ровно тот класс
  # тишины, из-за которого сайт стоял месяц.
  echo "[notify] НЕТ NOTIFY_BOT_TOKEN/NOTIFY_CHAT_ID в .env — сообщение не отправлено: $*" >&2
  exit 1
fi

case "$SEVERITY" in
  critical) ICON="🚨" ;;
  warn)     ICON="⚠️" ;;
  info)     ICON="ℹ️" ;;
  ok)       ICON="✅" ;;
  *)        ICON="📌" ;;
esac

HOST=$(hostname)
TS=$(date "+%Y-%m-%d %H:%M:%S %Z")

TEXT="${ICON} *ai-daily / ${SEVERITY}*
${MESSAGE}

\`${HOST}\` · ${TS}"

curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
  -d "chat_id=${TG_CHAT_ID}" \
  -d "parse_mode=Markdown" \
  --data-urlencode "text=${TEXT}" > /dev/null
