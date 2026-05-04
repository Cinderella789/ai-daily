(async function () {
  const listEl = document.getElementById("news-list");
  const metaEl = document.getElementById("meta");
  const filtersEl = document.getElementById("filters");
  const sourceFiltersEl = document.getElementById("source-filters");
  const searchEl = document.getElementById("search");

  let items = [];
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

  function buildSourceButtons() {
    // Считаем счётчики по источникам, сортируем по убыванию
    const counts = {};
    for (const it of items) {
      const s = it.source || "—";
      counts[s] = (counts[s] || 0) + 1;
    }
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);

    // Обновляем счётчик у "Все"
    const allBtn = sourceFiltersEl.querySelector('[data-source="all"]');
    if (allBtn) allBtn.innerHTML = `Все<span class="count">${items.length}</span>`;

    // Добавляем по кнопке на каждый источник
    for (const [source, n] of sorted) {
      const btn = document.createElement("button");
      btn.className = "filter-btn";
      btn.dataset.source = source;
      btn.innerHTML = `${source}<span class="count">${n}</span>`;
      sourceFiltersEl.appendChild(btn);
    }
  }

  function render() {
    let filtered = items;
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
      return `
        <article class="news-card">
          <div class="topbar">
            <span class="topic">${it.topic || ""}</span>
            <span>${it.source || ""}</span>
            <span>· ${date}</span>
          </div>
          <h2><a href="${it.url}" target="_blank" rel="noopener">${highlight(titleRaw, query)}</a></h2>
          <p>${highlight(summaryRaw, query)}${summaryRaw.length >= 320 ? "…" : ""}</p>
        </article>
      `;
    }).join("");
  }

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

  try {
    const res = await fetch("./data/latest.json", { cache: "no-store" });
    const payload = await res.json();
    items = payload.items || [];
    const ts = new Date(payload.generated_at).toLocaleString("ru-RU");
    metaEl.textContent = `Обновлено: ${ts} · всего материалов: ${items.length}`;
    buildSourceButtons();
    render();
  } catch (err) {
    listEl.innerHTML = `<p class="empty">Не удалось загрузить новости: ${err.message}</p>`;
  }
})();
