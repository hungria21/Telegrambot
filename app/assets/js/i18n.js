/*
 * i18n: carrega arquivos de tradução de /i18n e aplica nos elementos
 * marcados com data-i18n / data-i18n-attr.
 */
(function(){
  "use strict";

  const AVAILABLE = ["pt-BR", "en", "es"];
  const DEFAULT_LANG = "pt-BR";
  const STORE_KEY = "bb-lang";

  let dict = {};
  let lang = DEFAULT_LANG;

  function get(key){
    return key.split(".").reduce((o,k)=> (o && o[k] != null) ? o[k] : undefined, dict);
  }

  function t(key, fallback){
    const v = get(key);
    return (typeof v === "string") ? v : (fallback != null ? fallback : key);
  }

  function apply(){
    document.documentElement.lang = lang;
    document.title = t("site.title", document.title);
    document.querySelectorAll("[data-i18n]").forEach(el => {
      el.textContent = t(el.getAttribute("data-i18n"), el.textContent);
    });
    document.querySelectorAll("[data-i18n-attr]").forEach(el => {
      el.getAttribute("data-i18n-attr").split(";").forEach(pair => {
        const [attr, key] = pair.split(":").map(s => s.trim());
        if(attr && key) el.setAttribute(attr, t(key, el.getAttribute(attr) || ""));
      });
    });
  }

  async function setLang(next){
    if(!AVAILABLE.includes(next)) next = DEFAULT_LANG;
    try{
      const res = await fetch("i18n/" + next + ".json");
      if(!res.ok) throw new Error(res.status);
      dict = await res.json();
      lang = next;
      localStorage.setItem(STORE_KEY, next);
    }catch(e){
      if(next !== DEFAULT_LANG) return setLang(DEFAULT_LANG);
      console.error("Falha ao carregar traduções:", e);
    }
    apply();
    document.dispatchEvent(new CustomEvent("i18n:changed", { detail:{ lang } }));
  }

  async function init(){
    const saved = localStorage.getItem(STORE_KEY);
    const browser = (navigator.language || "").slice(0,2);
    const guess = AVAILABLE.find(l => l.toLowerCase().startsWith(browser)) || DEFAULT_LANG;
    await setLang(saved || guess);
  }

  window.I18N = { init, setLang, t, get lang(){ return lang; }, AVAILABLE };
})();
