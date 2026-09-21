#!/bin/bash
# Запускается раз в час по cron. Проверяет состояние пайплайна.
# Шлёт алерт если:
#  - последний УСПЕШНЫЙ update был >6 часов назад
#  - последний дайджест был >36 часов назад
#  - state-файл с алертом существует (значит был сбой в pipeline)
set +e
cd ~/ai-daily

# NOTIFY переопределяется для прогонов вручную: NOTIFY=echo ./health-watch.sh
NOTIFY=${NOTIFY:-~/ai-daily/notify.sh}
STATE_DIR=~/ai-daily/data/.health
mkdir -p "$STATE_DIR"

NOW=$(date +%s)

# === 1) Проверка последнего успешного update ===
# Успешный = в логе есть "[push] изменения отправлены" или "[push] нет изменений"
LAST_OK_LOG=$(grep -l "\[push\] изменения отправлены\|\[push\] нет изменений" ~/ai-daily/logs/update-*.log 2>/dev/null | tail -1)

if [ -z "$LAST_OK_LOG" ]; then
  # 21.09: эта ветка слала critical КАЖДЫЙ ЧАС без всякого троттла (и выходила
  # до остальных проверок), а текст врал: пайплайн собирал новости и слал их в
  # Telegram, не проходил только git push. Месяц по ~28 сообщений в сутки —
  # так алерты и приучают себя игнорировать. Теперь: раз в 12 ч, с возрастом
  # поломки в тексте и по существу.
  AHEAD=$(git -C ~/ai-daily rev-list --count @{u}..HEAD 2>/dev/null || echo "?")
  ORIGIN_DATE=$(git -C ~/ai-daily log -1 --format=%ad --date=short @{u} 2>/dev/null || echo "?")
  FIRST_FAIL=$(grep -l "провалился после 5 попыток" ~/ai-daily/logs/update-*.log 2>/dev/null | head -1)
  if [ -n "$FIRST_FAIL" ]; then
    FAIL_DAYS=$(( (NOW - $(stat -c %Y "$FIRST_FAIL")) / 86400 ))
  else
    FAIL_DAYS="?"
  fi
  NOPUSH_ALERT="$STATE_DIR/last-nopush-alerted"
  LAST_NP=$(cat "$NOPUSH_ALERT" 2>/dev/null || echo 0)
  if [ $((NOW - LAST_NP)) -gt 43200 ]; then
    $NOTIFY critical "git push не проходит ${FAIL_DAYS} сут: ${AHEAD} коммитов не отправлено, на GitHub последнее ${ORIGIN_DATE} — сайт на Cloudflare с тех пор НЕ обновляется. Сбор новостей и Telegram при этом работают, поэтому со стороны канала поломка не видна."
    echo $NOW > "$NOPUSH_ALERT"
  fi
fi

# ⚠️ Здесь раньше стоял `exit 0` (21.09): ветка «нет успешных прогонов» не
# только слала critical каждый час, но и ОБРЫВАЛА скрипт — проверки свежего
# лога, дайджеста и сайта не выполнялись вовсе. То есть самая шумная ветка
# глушила все остальные. Теперь дальше идём всегда, а то, что считается от
# последнего успешного лога, просто пропускаем.
if [ -n "$LAST_OK_LOG" ]; then
LAST_OK_TS=$(stat -c %Y "$LAST_OK_LOG")
DELTA=$((NOW - LAST_OK_TS))
DELTA_H=$((DELTA / 3600))

ALERT_FILE="$STATE_DIR/last-update-alerted"
LAST_ALERT_TS=$(cat "$ALERT_FILE" 2>/dev/null || echo 0)
SINCE_ALERT=$((NOW - LAST_ALERT_TS))

# Cron работает каждые 4 часа, плюс буфер => алерт если >6 часов
if [ $DELTA -gt 21600 ]; then
  # шлём не чаще раза в 4 часа
  if [ $SINCE_ALERT -gt 14400 ]; then
    LAST_LOG_NAME=$(basename "$LAST_OK_LOG")
    $NOTIFY critical "Последний успешный update был $DELTA_H ч назад ($LAST_LOG_NAME). Cron должен был отработать."
    echo $NOW > "$ALERT_FILE"
  fi
fi
fi   # конец блока «есть успешный лог»

# === 2) Проверка последнего лога обновления — даже если он есть, может в нём ошибка ===
LATEST_LOG=$(ls -t ~/ai-daily/logs/update-*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
  LATEST_TS=$(stat -c %Y "$LATEST_LOG")
  AGE=$((NOW - LATEST_TS))
  # лог моложе часа но без push
  if [ $AGE -lt 3600 ] && ! grep -q "\[push\] изменения отправлены\|\[push\] нет изменений" "$LATEST_LOG"; then
    FAIL_ALERT="$STATE_DIR/last-fail-alerted"
    LAST_FAIL_TS=$(cat "$FAIL_ALERT" 2>/dev/null || echo 0)
    if [ $LATEST_TS -gt $LAST_FAIL_TS ]; then
      LATEST_NAME=$(basename "$LATEST_LOG")
      LAST_LINE=$(tail -1 "$LATEST_LOG" | head -c 150)
      $NOTIFY critical "Свежий update упал не дойдя до push. Лог: $LATEST_NAME. Последняя строка: $LAST_LINE"
      echo $LATEST_TS > "$FAIL_ALERT"
    fi
  fi
fi

# === 4) ПРОВЕРКА ВЫХОДА: обновился ли САЙТ (21.09) ===
# Зачем: месяц (20.08-21.09) сайт стоял, а все проверки были зелёными — они
# смотрели на ШАГИ пайплайна, а выход никто не проверял. Сломался git push,
# Telegram при этом работал (отдельный токен), и поломку не было видно.
# Здесь сравниваем дату свежей новости НА САЙТЕ с локальной: расходятся —
# значит до Cloudflare данные не доехали, чем бы это ни было вызвано.
SITE_URL="${SITE_URL:-https://ai-daily-9au.pages.dev/data/latest.json}"   # переопределяется для проверки
SITE_MAX_LAG_H="${SITE_MAX_LAG_H:-8}"     # cron каждые 4 ч + сборка Pages
FAILS_FILE="$STATE_DIR/site-curl-fails"

gen_at() {  # вытащить generated_at из json на stdin
  head -c 400 | grep -o '"generated_at": *"[^"]*"' | head -1 | cut -d'"' -f4
}

LOCAL_GEN=$(gen_at < ~/ai-daily/data/latest.json 2>/dev/null)
SITE_GEN=$(curl -s --max-time 20 "$SITE_URL" 2>/dev/null | gen_at)

if [ -z "$SITE_GEN" ]; then
  # Сеть/Pages не ответили. Молчать нельзя — но и алертить на один сбой тоже:
  # тревожим после 3 неудач подряд, то есть 3 часов недоступности.
  FAILS=$(( $(cat "$FAILS_FILE" 2>/dev/null || echo 0) + 1 ))
  echo $FAILS > "$FAILS_FILE"
  if [ $FAILS -ge 3 ] && [ $((FAILS % 12)) -eq 3 ]; then
    $NOTIFY warn "Сайт не отвечает ${FAILS} ч подряд ($SITE_URL) — проверить Cloudflare Pages."
  fi
elif [ -n "$LOCAL_GEN" ]; then
  echo 0 > "$FAILS_FILE"
  LOCAL_TS=$(date -d "$LOCAL_GEN" +%s 2>/dev/null || echo 0)
  SITE_TS=$(date -d "$SITE_GEN" +%s 2>/dev/null || echo 0)
  LAG=$(( LOCAL_TS - SITE_TS ))
  LAG_H=$(( LAG / 3600 ))
  if [ $LAG -gt $((SITE_MAX_LAG_H * 3600)) ]; then
    SITE_ALERT="$STATE_DIR/last-site-alerted"
    LAST_SA=$(cat "$SITE_ALERT" 2>/dev/null || echo 0)
    if [ $((NOW - LAST_SA)) -gt 43200 ]; then
      # Тон растёт с возрастом: молчать про застарелое нельзя, но и кричать
      # одинаково про 9 часов и про месяц — значит обесценить оба сообщения.
      TONE=""
      [ $LAG_H -ge 48 ] && TONE=" 🚨 Это уже $((LAG_H / 24)) сут — НЕ УСТРАНЕНО."
      $NOTIFY critical "Сайт отстаёт от локальных данных на ${LAG_H} ч.${TONE} На Pages ${SITE_GEN}, локально ${LOCAL_GEN}. Пайплайн считает, но до сайта данные НЕ доезжают (так было 20.08-21.09: молча падал git push)."
      echo $NOW > "$SITE_ALERT"
    fi
  fi
fi

# === 3) Проверка дайджеста ===
LAST_DIGEST_DATE=$(cat ~/ai-daily/data/.last-digest-date.txt 2>/dev/null || echo "")
if [ -n "$LAST_DIGEST_DATE" ]; then
  LAST_DIGEST_TS=$(date -d "$LAST_DIGEST_DATE" +%s 2>/dev/null || echo 0)
  DIGEST_AGE=$((NOW - LAST_DIGEST_TS))
  DIGEST_AGE_H=$((DIGEST_AGE / 3600))
  if [ $DIGEST_AGE -gt 129600 ]; then  # 36 часов
    DIGEST_ALERT="$STATE_DIR/last-digest-alerted"
    LAST_DA_TS=$(cat "$DIGEST_ALERT" 2>/dev/null || echo 0)
    SINCE_DA=$((NOW - LAST_DA_TS))
    if [ $SINCE_DA -gt 43200 ]; then  # не чаще раза в 12 часов
      $NOTIFY warn "Дайджест не отправлялся $DIGEST_AGE_H ч (последний $LAST_DIGEST_DATE)."
      echo $NOW > "$DIGEST_ALERT"
    fi
  fi
fi
