(async function () {
  const $ = (id) => document.getElementById(id);
  const listEl = $("news-list");
  const metaEl = $("meta");
  const pagerEl = $("pager");
  const searchEl = $("search");
  const categoryEl = $("category-filter");
  const topicEl = $("topic-filter");
  const sourceEl = $("source-filter");
  const periodEl = $("period-filter");

  const PAGE_SIZE = 25;
  let items = [];
  let page = 1;
  let debounceId = 0;

  function uniq(arr) {
    return Array.from(new Set(arr)).filter(Boolean).sort();
  }

  function fillSelect(sel, values) {
    for (const v of values) {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = v;
      sel.appendChild(opt);
    }
  }

  function getQuery() {
    return {
      q: searchEl.value.trim().toLowerCase(),
      category: categoryEl.value,
      topic: topicEl.value,
      source: sourceEl.value,
      period: periodEl.value,
    };
  }

  function applyFilters() {
    const { q, category, topic, source, period } = getQuery();
    let cutoff = 0;
    if (period !== "all") {
      cutoff = Date.now() - Number(period) * 24 * 3600 * 1000;
    }
    return items.filter((it) => {
      if (category !== "all" && (it.category || "ai") !== category) return false;
      if (topic !== "all" && it.topic !== topic) return false;
      if (source !== "all" && it.source !== source) return false;
      if (cutoff && new Date(it.published_at).getTime() < cutoff) return false;
      if (q) {
        const hay = (
          (it.title_ru || "") + " " +
          (it.title_en || "") + " " +
          (it.summary_ru || "") + " " +
          (it.summary_en || "")
        ).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  function highlight(text, q) {
    if (!q) return text;
    const idx = text.toLowerCase().indexOf(q);
    if (idx < 0) return text;
    const end = idx + q.length;
    return (
      text.slice(0, idx) +
      `<mark>${text.slice(idx, end)}</mark>` +
      text.slice(end)
    );
  }

  function render() {
    const filtered = applyFilters();
    const { q } = getQuery();

    metaEl.textContent = `Найдено: ${filtered.length} из ${items.length}`;

    if (!filtered.length) {
      listEl.innerHTML = '<p class="empty">Ничего не найдено.</p>';
      pagerEl.innerHTML = "";
      return;
    }

    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    if (page > totalPages) page = totalPages;
    const start = (page - 1) * PAGE_SIZE;
    const slice = filtered.slice(start, start + PAGE_SIZE);

    listEl.innerHTML = slice.map((it) => {
      const titleRaw = it.title_ru || it.title_en || "Без заголовка";
      const summaryRaw = (it.summary_ru || it.summary_en || "").slice(0, 320);
      const date = new Date(it.published_at).toLocaleString("ru-RU", {
        day: "numeric", month: "short", year: "numeric",
        hour: "2-digit", minute: "2-digit",
      });
      const title = highlight(titleRaw, q);
      const summary = highlight(summaryRaw, q);
      const catBadge = it.category === "crypto"
        ? '<span class="cat-badge crypto">₿ Crypto</span>'
        : '<span class="cat-badge ai">🤖 AI</span>';
      return `
        <article class="news-card">
          <div class="topbar">
            ${catBadge}
            <span class="topic">${it.topic || ""}</span>
            <span>${it.source || ""}</span>
            <span>· ${date}</span>
          </div>
          <h2><a href="${it.url}" target="_blank" rel="noopener">${title}</a></h2>
          <p>${summary}${summaryRaw.length >= 320 ? "…" : ""}</p>
        </article>
      `;
    }).join("");

    pagerEl.innerHTML = totalPages > 1
      ? `
        <button id="prev" ${page === 1 ? "disabled" : ""}>← Назад</button>
        <span>Страница ${page} из ${totalPages}</span>
        <button id="next" ${page === totalPages ? "disabled" : ""}>Вперёд →</button>
      `
      : "";
    const prev = $("prev"), next = $("next");
    if (prev) prev.onclick = () => { page--; render(); window.scrollTo(0, 0); };
    if (next) next.onclick = () => { page++; render(); window.scrollTo(0, 0); };
  }

  function debouncedRender() {
    clearTimeout(debounceId);
    debounceId = setTimeout(() => { page = 1; render(); }, 150);
  }

  searchEl.addEventListener("input", debouncedRender);
  categoryEl.addEventListener("change", debouncedRender);
  topicEl.addEventListener("change", debouncedRender);
  sourceEl.addEventListener("change", debouncedRender);
  periodEl.addEventListener("change", debouncedRender);

  try {
    const res = await fetch("./data/archive.json", { cache: "no-store" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const payload = await res.json();
    items = payload.items || [];
    fillSelect(topicEl, uniq(items.map((i) => i.topic)));
    fillSelect(sourceEl, uniq(items.map((i) => i.source)));
    render();
  } catch (err) {
    listEl.innerHTML = `<p class="empty">Не удалось загрузить архив: ${err.message}.<br>
      Архив наполняется при первом запуске GitHub Action <code>update-news</code>.</p>`;
  }
})();
