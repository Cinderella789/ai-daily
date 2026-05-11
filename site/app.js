(async function () {
  const listEl = document.getElementById("news-list");
  const metaEl = document.getElementById("meta");
  const filtersEl = document.getElementById("filters");
  const sourceFiltersEl = document.getElementById("source-filters");
  const categoryTabsEl = document.getElementById("category-tabs");
  const searchEl = document.getElementById("search");

  // Темы по категориям (синхронизировано со scripts/sources.py)
  const TOPICS_AI = ["Models", "Hardware", "Regulations", "Startups", "Research", "AI Agents", "Corporate AI"];
  const TOPICS_CRYPTO = ["Bitcoin", "Ethereum", "DeFi", "Altcoins", "Regulations", "Hacks", "Macro", "NFT & Gaming"];

  let items = [];
  let activeCategory = "all";
  let activeTopic = "all";
  let activeSource = "all";
  let query = "";
  let debounceId = 0;

  function highlight(text, q) {
    if (!q) return text;
    const idx = text.toLowerCase().indexOf(q);
    if (idx < 0) return text;
    const end = idx + q.length;
    return text.slice(0, idx) + `<mark>${text.slice(idx, end)}</mark>` + text.slice(end);
  }

  function getTopicsForCategory(cat) {
    if (cat === "ai") return TOPICS_AI;
    if (cat === "crypto") return TOPICS_CRYPTO;
    // Для "all" — объединение без дублей, AI первыми
    const seen = new Set();
    return [...TOPICS_AI, ...TOPICS_CRYPTO].filter((t) => {
      if (seen.has(t)) return false;
      seen.add(t);
      return true;
    });
  }

  function rebuildTopicButtons() {
    // Очищаем кнопки тем кроме первой (Все)
    const allBtn = filtersEl.querySelector('[data-topic="all"]');
    filtersEl.innerHTML = '<span class="filter-label">Тема:</span>';
    if (allBtn) {
      filtersEl.appendChild(allBtn);
    } else {
      const btn = document.createElement("button");
      btn.className = "filter-btn active";
      btn.dataset.topic = "all";
      btn.textContent = "Все";
      filtersEl.appendChild(btn);
    }

    // Считаем сколько новостей по каждой теме в текущей категории
    const filtered = activeCategory === "all" ? items : items.filter((it) => it.category === activeCategory);
    const counts = {};
    for (const it of filtered) {
      const t = it.topic || "—";
      counts[t] = (counts[t] || 0) + 1;
    }

    const topics = getTopicsForCategory(activeCategory);
    for (const t of topics) {
      const n = counts[t] || 0;
      if (n === 0) continue;
      const btn = document.createElement("button");
      btn.className = "filter-btn" + (activeTopic === t ? " active" : "");
      btn.dataset.topic = t;
      btn.innerHTML = `${t}<span class="count">${n}</span>`;
      filtersEl.appendChild(btn);
    }

    // Обновляем "Все" — счётчик
    const allBtnNow = filtersEl.querySelector('[data-topic="all"]');
    if (allBtnNow) {
      allBtnNow.innerHTML = `Все<span class="count">${filtered.length}</span>`;
      allBtnNow.classList.toggle("active", activeTopic === "all");
    }
  }

  function rebuildSourceButtons() {
    sourceFiltersEl.innerHTML = '<span class="filter-label">Источник:</span>' +
      '<button class="filter-btn active" data-source="all">Все</button>';

    // Источники только из выбранной категории
    const filtered = activeCategory === "all" ? items : items.filter((it) => it.category === activeCategory);
    const counts = {};
    for (const it of filtered) {
      const s = it.source || "—";
      counts[s] = (counts[s] || 0) + 1;
    }
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

    const allBtn = sourceFiltersEl.querySelector('[data-source="all"]');
    if (allBtn) allBtn.innerHTML = `Все<span class="count">${filtered.length}</span>`;

    for (const [source, n] of sorted) {
      const btn = document.createElement("button");
      btn.className = "filter-btn";
      btn.dataset.source = source;
      btn.innerHTML = `${source}<span class="count">${n}</span>`;
      sourceFiltersEl.appendChild(btn);
    }

    // Если активный source не в текущей категории — сбрасываем на all
    if (activeSource !== "all" && !counts[activeSource]) {
      activeSource = "all";
    }
  }

  function categoryBadge(cat) {
    if (cat === "crypto") return '<span class="cat-badge crypto">₿ Crypto</span>';
    if (cat === "ai") return '<span class="cat-badge ai">🤖 AI</span>';
    return "";
  }

  function render() {
    let filtered = items;
    if (activeCategory !== "all") filtered = filtered.filter((it) => it.category === activeCategory);
    if (activeTopic !== "all") filtered = filtered.filter((it) => it.topic === activeTopic);
    if (activeSource !== "all") filtered = filtered.filter((it) => it.source === activeSource);

    if (query) {
      filtered = filtered.filter((it) => {
        const hay = (
          (it.title_ru || "") + " " +
          (it.title_en || "") + " " +
          (it.summary_ru || "") + " " +
          (it.summary_en || "")
        ).toLowerCase();
        return hay.includes(query);
      });
    }

    if (!filtered.length) {
      listEl.innerHTML = '<p class="empty">Ничего не найдено по выбранным фильтрам.</p>';
      return;
    }

    listEl.innerHTML = filtered.map((it) => {
      const titleRaw = it.title_ru || it.title_en || "Без заголовка";
      const summaryRaw = (it.summary_ru || it.summary_en || "").slice(0, 320);
      const date = new Date(it.published_at).toLocaleString("ru-RU", {
        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
      });
      const dups = Array.isArray(it.duplicates) ? it.duplicates : [];
      const dupHtml = dups.length
        ? `<div class="duplicates"><span class="dup-label">Также об этом:</span> ${dups
            .map((d) => `<a href="${d.url}" target="_blank" rel="noopener">${d.source || "источник"}</a>`)
            .join(" · ")}</div>`
        : "";
      return `
        <article class="news-card">
          <div class="topbar">
            ${categoryBadge(it.category)}
            <span class="topic">${it.topic || ""}</span>
            <span>${it.source || ""}</span>
            <span>· ${date}</span>
            ${dups.length ? `<span class="dup-badge">+${dups.length}</span>` : ""}
          </div>
          <h2><a href="${it.url}" target="_blank" rel="noopener">${highlight(titleRaw, query)}</a></h2>
          <p>${highlight(summaryRaw, query)}${summaryRaw.length >= 320 ? "…" : ""}</p>
          ${dupHtml}
        </article>
      `;
    }).join("");
  }

  // Обработчик клика по вкладкам категорий
  categoryTabsEl.addEventListener("click", (e) => {
    const btn = e.target.closest(".category-tab");
    if (!btn) return;
    categoryTabsEl.querySelectorAll(".category-tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeCategory = btn.dataset.category;
    // Сбрасываем фильтры при смене категории
    activeTopic = "all";
    activeSource = "all";
    rebuildTopicButtons();
    rebuildSourceButtons();
    render();
  });

  filtersEl.addEventListener("click", (e) => {
    const btn = e.target.closest(".filter-btn");
    if (!btn) return;
    filtersEl.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeTopic = btn.dataset.topic;
    render();
  });

  sourceFiltersEl.addEventListener("click", (e) => {
    const btn = e.target.closest(".filter-btn");
    if (!btn) return;
    sourceFiltersEl.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeSource = btn.dataset.source;
    render();
  });

  if (searchEl) {
    searchEl.addEventListener("input", () => {
      clearTimeout(debounceId);
      debounceId = setTimeout(() => {
        query = searchEl.value.trim().toLowerCase();
        render();
      }, 120);
    });
  }

  function humanAgo(d) {
    const diff = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diff < 60) return "только что";
    if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`;
    return `${Math.floor(diff / 86400)} дн назад`;
  }

  try {
    const res = await fetch("./data/latest.json", { cache: "no-store" });
    const payload = await res.json();
    items = (payload.items || []).map((it) => ({ ...it, category: it.category || "ai" }));

    // Считаем по категориям для подписи в табах
    const aiCount = items.filter((it) => it.category === "ai").length;
    const cryptoCount = items.filter((it) => it.category === "crypto").length;
    const allBtn = categoryTabsEl.querySelector('[data-category="all"]');
    const aiBtn = categoryTabsEl.querySelector('[data-category="ai"]');
    const cryptoBtn = categoryTabsEl.querySelector('[data-category="crypto"]');
    if (allBtn) allBtn.innerHTML = `Всё<span class="count">${items.length}</span>`;
    if (aiBtn) aiBtn.innerHTML = `🤖 AI<span class="count">${aiCount}</span>`;
    if (cryptoBtn) cryptoBtn.innerHTML = `₿ Crypto<span class="count">${cryptoCount}</span>`;

    const updatedAt = new Date(payload.generated_at);
    const ts = updatedAt.toLocaleString("ru-RU", {
      day: "numeric", month: "long", hour: "2-digit", minute: "2-digit",
      timeZone: "Europe/Moscow",
    });
    const ago = humanAgo(updatedAt);
    metaEl.innerHTML = `Обновлено: ${ts} MSK <span class="ago">(${ago})</span> · ${items.length} материалов за сутки`;

    rebuildTopicButtons();
    rebuildSourceButtons();
    render();
  } catch (err) {
    listEl.innerHTML = `<p class="empty">Не удалось загрузить новости: ${err.message}</p>`;
  }
})();
