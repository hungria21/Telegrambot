/*
 * Parser mínimo de frontmatter (YAML simples) para os posts .md.
 * Suporta pares chave: valor, listas "[a, b]" e listas com "- item".
 */
(function(){
  "use strict";

  function parseValue(raw){
    const v = raw.trim();
    if(v.startsWith("[") && v.endsWith("]")){
      return v.slice(1,-1).split(",").map(s=>s.trim().replace(/^["']|["']$/g,"")).filter(Boolean);
    }
    if(v === "true") return true;
    if(v === "false") return false;
    return v.replace(/^["']|["']$/g,"");
  }

  function parseFrontmatter(text){
    const match = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
    if(!match) return { data:{}, body:text };
    const data = {};
    const lines = match[1].split(/\r?\n/);
    let lastKey = null;
    for(const line of lines){
      const kv = line.match(/^([A-Za-z0-9_.-]+)\s*:\s*(.*)$/);
      if(kv){
        lastKey = kv[1];
        const val = kv[2];
        data[lastKey] = val === "" ? [] : parseValue(val);
      } else {
        const item = line.match(/^\s*-\s+(.+)$/);
        if(item && lastKey){
          if(!Array.isArray(data[lastKey])) data[lastKey] = [];
          data[lastKey].push(parseValue(item[1]));
        }
      }
    }
    return { data, body: match[2].trim() };
  }

  window.MD = { parseFrontmatter };
})();
