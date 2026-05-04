(async function () {
  const listEl = document.getElementById("news-list");
  const metaEl = document.getElementById("meta");
  const filtersEl = document.getElementById("filters");
  const searchEl = document.getElementById("search");

  let items = [];
  let activeTopic = "all";
  let query = "";
  let debounceId = 0;

  function highlight(text, q) {
    if (!q) return text;
    const idx = text.toLowerCase().indexOf(q);
    if (idx < 0) return text;
    const end = idx + q.length;
    return text.slice(0, idx) + `<mark>${text.slice(idx, end)}</mark>` + text.slice(end);
  }

  function render() {
    let filtered = activeTopic === "all"
      ? items
      : items.filter((it) => it.topic === activeTopic);

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
      listEl.innerHTML = '<p class="empty">Ничего не найдено.</p>';
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
    document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    activeTopic = btn.dataset.topic;
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
    render();
  } catch (err) {
    listEl.innerHTML = `<p class="empty">Не удалось загрузить новости: ${err.message}</p>`;
  }
})();
