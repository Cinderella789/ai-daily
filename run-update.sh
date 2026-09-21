#!/bin/bash
# Полный цикл обновления новостей. Запускается по cron каждые 4 часа.
set -e
cd ~/ai-daily

# Подгружаем .env в окружение
set -a
source .env
set +a

LOG=$HOME/ai-daily/logs/update-$(date +%Y-%m-%d_%H-%M).log
mkdir -p $HOME/ai-daily/logs

{
  echo "=== run-update started:" $(date -Iseconds)

  echo "--- git pull (с автовосстановлением) ---"
  if ! git diff --quiet HEAD --; then
    echo "[warn] есть незакоммиченные изменения в репо, откатываю"
    git checkout -- .
  fi
  git pull --rebase --quiet || {
    echo "[error] git pull упал, пробую сбросить и перетянуть"
    git rebase --abort 2>/dev/null || true
    git fetch --quiet
    git reset --hard origin/main
  }

  echo "--- fetch ---"
  .venv/bin/python -m scripts.fetch_feeds

  echo "--- classify ---"
  .venv/bin/python -m scripts.classify_news

  echo "--- translate ---"
  .venv/bin/python -m scripts.translate_news

  echo "--- dedup ---"
  # set +e только для dedup — если упадёт по OOM или сети, продолжаем без него
  set +e
  .venv/bin/python -m scripts.dedup_news
  dedup_status=$?
  set -e
  if [ $dedup_status -ne 0 ]; then
    echo "[warn] dedup упал с кодом $dedup_status, продолжаю без дедупликации"
  fi

  echo "--- archive ---"
  .venv/bin/python -m scripts.append_archive

  echo "--- mirror ---"
  mkdir -p site/data
  cp data/latest.json site/data/latest.json
  cp data/archive.json site/data/archive.json

  echo "--- commit & push ---"
  # set +e на всю секцию: git add может упасть на отсутствующих файлах,
  # push — на 500 от GitHub. Не валим cron.
  set +e
  git add data/latest.json site/data/latest.json data/archive.json site/data/archive.json 2>/dev/null
  git add cache/.translation-cache.json cache/.embeddings-cache.json 2>/dev/null
  if ! git diff --cached --quiet; then
    git commit -m "chore: refresh news $(date -u +%FT%TZ)"
    # retry push: GitHub иногда отвечает 500
    push_ok=0
    for attempt in 1 2 3 4 5; do
      if git push 2>&1; then
        push_ok=1
        echo "[push] изменения отправлены (попытка $attempt)"
        break
      fi
      echo "[push] попытка $attempt не удалась, жду 15 сек"
      sleep 15
    done
    if [ $push_ok -eq 0 ]; then
      echo "[error] git push провалился после 5 попыток"
      # Троттл 12 ч (21.09): прогон идёт 4 раза в сутки, и при затяжной
      # поломке это было 4 одинаковых critical в день ПОВЕРХ ежечасного
      # health-watch. Состояние «push не идёт N суток» сторожит health-watch,
      # здесь достаточно одного сообщения о самом событии.
      PUSH_ALERT=~/ai-daily/data/.health/last-push-alerted
      mkdir -p "$(dirname "$PUSH_ALERT")"
      LAST_PA=$(cat "$PUSH_ALERT" 2>/dev/null || echo 0)
      if [ $(( $(date +%s) - LAST_PA )) -gt 43200 ]; then
        ~/ai-daily/notify.sh critical "git push провалился после 5 попыток. Лог: $(basename $LOG)"
        date +%s > "$PUSH_ALERT"
      fi
    fi
  else
    echo "[push] нет изменений"
  fi
  set -e
  echo "--- telegram ---"
  .venv/bin/python scripts/send_telegram.py || echo "[tg] WARN: не отправлено, продолжаем"

  echo "=== done:" $(date -Iseconds)
} 2>&1 | tee $LOG

# Чистим логи старше 30 дней
find $HOME/ai-daily/logs -name "update-*.log" -mtime +30 -delete 2>/dev/null || true
