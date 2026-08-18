(function(){
  "use strict";

  const $ = (sel) => document.querySelector(sel);
  const resultsEl = $("#results");
  const emptyEl = $("#emptyState");
  const sectionLabel = $("#sectionLabel");
  const input = $("#searchInput");
  const field = $("#searchField");
  const clearBtn = $("#clearBtn");
  const sheet = $("#sheet");
  const scrim = $("#scrim");
  const settingsBtn = $("#settingsBtn");
  const themeMeta = $("#themeColorMeta");
  const themeSub = $("#themeSub");
  const langChips = $("#langChips");
  const themeChips = $("#themeChips");

  const THEME_KEY = "bb-theme";
  const THEME_COLORS = { dark:"#0F1320", light:"#F4F6FB" };

  let bots = [];
  let loaded = false;

  /* ---------- Tema ---------- */
  function applyTheme(theme){
    if(theme !== "light") theme = "dark";
    document.documentElement.setAttribute("data-theme", theme);
    themeMeta.setAttribute("content", THEME_COLORS[theme]);
    themeSub.textContent = I18N.t("settings.theme.active." + theme);
    themeChips.querySelectorAll(".chip").forEach(c =>
      c.classList.toggle("active", c.dataset.themeOption === theme));
    localStorage.setItem(THEME_KEY, theme);
  }
  themeChips.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-theme-option]");
    if(btn) applyTheme(btn.dataset.themeOption);
  });

  /* ---------- Idioma ---------- */
  const LANG_LABELS = { "pt-BR":"Português", "en":"English", "es":"Español" };
  function renderLangChips(){
    langChips.innerHTML = "";
    I18N.AVAILABLE.forEach(code => {
      const b = document.createElement("button");
      b.className = "chip" + (code === I18N.lang ? " active" : "");
      b.textContent = LANG_LABELS[code] || code;
      b.addEventListener("click", () => I18N.setLang(code));
      langChips.appendChild(b);
    });
  }
  document.addEventListener("i18n:changed", () => {
    renderLangChips();
    applyTheme(localStorage.getItem(THEME_KEY) || "dark"); // re-atualiza o subtítulo do tema
    if(loaded) runSearch(); // re-renderiza rótulos ("Em alta"/"Resultados")
  });

  /* ---------- Carregamento dos bots (.md) ---------- */
  function escapeHtml(s){
    return String(s).replace(/[&<>"']/g, c => ({
      "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
    }[c]));
  }

  async function loadBots(){
    sectionLabel.style.display = "none";
    resultsEl.innerHTML = '<div class="loading">' + escapeHtml(I18N.t("loading")) + "</div>";
    try{
      const manifestRes = await fetch("content/bots/index.json");
      if(!manifestRes.ok) throw new Error("manifest " + manifestRes.status);
      const files = await manifestRes.json();

      const items = await Promise.all(files.map(async file => {
        const res = await fetch("content/bots/" + encodeURIComponent(file));
        if(!res.ok) return null;
        const { data } = window.MD.parseFrontmatter(await res.text());
        if(!data.username || !data.name) return null;
        return {
          name: String(data.name),
          username: String(data.username).replace(/^@/,""),
          description: String(data.description || ""),
          stats: String(data.stats || ""),
          image: data.image ? String(data.image) : null,
          color: Array.isArray(data.color) && data.color.length >= 2 ? data.color : ["#5B8DEF","#3E63C9"],
          tags: Array.isArray(data.tags) ? data.tags.map(String) : [],
          featured: data.featured === true
        };
      }));

      bots = items.filter(Boolean);
      // Em alta primeiro, mantendo a ordem do manifest dentro de cada grupo
      bots.sort((a,b) => (b.featured === true) - (a.featured === true));
      loaded = true;
      runSearch();
    }catch(err){
      console.error(err);
      loaded = true;
      resultsEl.innerHTML = "";
      sectionLabel.style.display = "none";
      emptyEl.classList.add("visible");
      emptyEl.querySelector("h2").textContent = I18N.t("error.title");
      emptyEl.querySelector("p").textContent = I18N.t("error.text");
    }
  }

  /* ---------- Renderização ---------- */
  function initials(name){
    return name.split(" ").filter(Boolean).slice(0,2).map(w=>w[0]).join("").toUpperCase();
  }

  function avatarHTML(bot){
    if(bot.image){
      return '<img class="avatar" src="' + escapeHtml(bot.image) + '" alt="" loading="lazy" ' +
        'onerror="this.outerHTML=this.dataset.fallback" data-fallback=\'' +
        escapeHtml('<div class="avatar" style="background:linear-gradient(135deg,' + bot.color[0] + ',' + bot.color[1] + ')">' + initials(bot.name) + "</div>") + '\'>';
    }
    return '<div class="avatar" style="background:linear-gradient(135deg,' + escapeHtml(bot.color[0]) + ',' + escapeHtml(bot.color[1]) + ')">' + escapeHtml(initials(bot.name)) + "</div>";
  }

  function cardHTML(bot){
    const stat = bot.stats
      ? '<div class="bot-stat"><svg viewBox="0 0 24 24" fill="none"><path d="M4 19c0-3.3 3.6-5 8-5s8 1.7 8 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="8" r="3.4" stroke="currentColor" stroke-width="1.8"/></svg>' + escapeHtml(bot.stats) + "</div>"
      : "";
    const tags = bot.tags.length
      ? '<div class="bot-tags">' + bot.tags.map(t => '<span class="bot-tag">' + escapeHtml(t) + "</span>").join("") + "</div>"
      : "";
    return (
      '<a class="bot-card" href="https://t.me/' + encodeURIComponent(bot.username) + '" target="_blank" rel="noopener">' +
        avatarHTML(bot) +
        '<div class="bot-info">' +
          '<div class="bot-name-row">' +
            '<span class="bot-name">' + escapeHtml(bot.name) + "</span>" +
            '<span class="bot-username">@' + escapeHtml(bot.username) + "</span>" +
          "</div>" +
          '<div class="bot-desc">' + escapeHtml(bot.description) + "</div>" +
          stat + tags +
        "</div>" +
      "</a>"
    );
  }

  function render(list, isSearch){
    if(!list.length){
      resultsEl.classList.add("hidden");
      resultsEl.innerHTML = "";
      emptyEl.classList.add("visible");
      emptyEl.querySelector("h2").textContent = I18N.t("empty.title");
      emptyEl.querySelector("p").textContent = I18N.t("empty.text");
      sectionLabel.style.display = "none";
      return;
    }
    emptyEl.classList.remove("visible");
    resultsEl.classList.remove("hidden");
    sectionLabel.style.display = "";
    sectionLabel.textContent = I18N.t(isSearch ? "sections.results" : "sections.featured");
    resultsEl.innerHTML = list.map(cardHTML).join("");
  }

  function runSearch(){
    const q = input.value.trim().toLowerCase();
    if(!q){ render(bots, false); return; }
    render(bots.filter(b =>
      b.name.toLowerCase().includes(q) ||
      b.username.toLowerCase().includes(q) ||
      b.description.toLowerCase().includes(q) ||
      b.tags.some(t => t.toLowerCase().includes(q))
    ), true);
  }

  /* ---------- Busca ---------- */
  let t;
  input.addEventListener("input", () => {
    field.classList.toggle("has-text", input.value.length > 0);
    clearTimeout(t);
    t = setTimeout(runSearch, 220);
  });
  clearBtn.addEventListener("click", () => {
    input.value = "";
    field.classList.remove("has-text");
    input.focus();
    runSearch();
  });

  /* ---------- Sheet de configurações ---------- */
  function openSheet(){
    sheet.classList.add("open");
    scrim.classList.add("open");
    settingsBtn.setAttribute("aria-expanded","true");
  }
  function closeSheet(){
    sheet.classList.remove("open");
    scrim.classList.remove("open");
    settingsBtn.setAttribute("aria-expanded","false");
  }
  settingsBtn.addEventListener("click", openSheet);
  scrim.addEventListener("click", closeSheet);
  document.addEventListener("keydown", (e) => { if(e.key === "Escape") closeSheet(); });

  /* ---------- Boot ---------- */
  (async function(){
    const savedTheme = localStorage.getItem(THEME_KEY);
    const prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
    await I18N.init();
    renderLangChips();
    applyTheme(savedTheme || (prefersLight ? "light" : "dark"));
    await loadBots();
  })();
})();
