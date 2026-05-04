(async function () {
  const listEl = document.getElementById("news-list");
  const metaEl = document.getElementById("meta");
  const filtersEl = document.getElementById("filters");

  let items = [];
  let activeTopic = "all";

  function render() {
    const filtered = activeTopic === "all"
      ? items
      : items.filter((it) => it.topic === activeTopic);

    if (!filtered.length) {
      listEl.innerHTML = '<p class="empty">Пока нет новостей в этой категории.</p>';
      return;
    }

    listEl.innerHTML = filtered.map((it) => {
      const title = it.title_ru || it.title_en || "Без заголовка";
      const summary = (it.summary_ru || it.summary_en || "").slice(0, 320);
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
          <h2><a href="${it.url}" target="_blank" rel="noopener">${title}</a></h2>
          <p>${summary}${summary.length >= 320 ? "…" : ""}</p>
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

  try {
    const res = await fetch("../data/latest.json", { cache: "no-store" });
    const payload = await res.json();
    items = payload.items || [];
    const ts = new Date(payload.generated_at).toLocaleString("ru-RU");
    metaEl.textContent = `Обновлено: ${ts} · всего материалов: ${items.length}`;
    render();
  } catch (err) {
    listEl.innerHTML = `<p class="empty">Не удалось загрузить новости: ${err.message}</p>`;
  }
})();
