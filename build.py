#!/usr/bin/env python3
"""
Compila todos os posts .md de content/bots/ em um único content/bots.json.

Rode localmente antes do commit (python3 build.py) ou deixe a GitHub Action
(.github/workflows/build-bots.yml) gerar automaticamente a cada push.
"""
import json
import os
import re
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BOTS_DIR = os.path.join(ROOT_DIR, "content", "bots")
OUT_FILE = os.path.join(ROOT_DIR, "content", "bots.json")

# Cache de listagens de pasta (evita reler o disco a cada imagem).
_dir_listing_cache = {}


def resolve_image_path(image_field):
    """
    Recebe o valor cru do campo 'image:' do .md (ex: 'images/bots/AirTrack.png')
    e devolve um caminho que realmente existe no disco, ignorando diferenças
    de maiúsculas/minúsculas entre o que foi escrito no .md e o nome real do
    arquivo. Isso evita imagens quebradas no site (GitHub Pages é case-sensitive).
    """
    if not image_field:
        return None

    # Caminho exatamente como escrito já existe -> não precisa de nada.
    exact_path = os.path.join(ROOT_DIR, image_field)
    if os.path.isfile(exact_path):
        return image_field

    # Não existe como escrito: procura na mesma pasta um arquivo cujo nome
    # bata ignorando maiúsculas/minúsculas.
    rel_dir = os.path.dirname(image_field)
    filename = os.path.basename(image_field)
    abs_dir = os.path.join(ROOT_DIR, rel_dir)

    if abs_dir not in _dir_listing_cache:
        try:
            _dir_listing_cache[abs_dir] = os.listdir(abs_dir)
        except FileNotFoundError:
            _dir_listing_cache[abs_dir] = []

    for real_name in _dir_listing_cache[abs_dir]:
        if real_name.lower() == filename.lower():
            # Reconstrói o caminho usando o nome real do arquivo no disco.
            fixed = "/".join([rel_dir, real_name]) if rel_dir else real_name
            print(f"Aviso: corrigida diferença de maiúsculas/minúsculas: "
                  f"'{image_field}' -> '{fixed}'", file=sys.stderr)
            return fixed

    # Não achou de jeito nenhum: mantém o valor original (vai cair no
    # fallback de iniciais no site, como já acontece hoje).
    print(f"Aviso: imagem não encontrada no disco: '{image_field}'", file=sys.stderr)
    return image_field


def parse_value(raw):
    v = raw.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1]
        return [s.strip().strip("\"'") for s in inner.split(",") if s.strip()]
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    return v.strip("\"'")


def parse_frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    data = {}
    last_key = None
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", line)
        if kv:
            last_key = kv.group(1)
            val = kv.group(2)
            data[last_key] = [] if val == "" else parse_value(val)
        else:
            item = re.match(r"^\s*-\s+(.+)$", line)
            if item and last_key is not None:
                if not isinstance(data.get(last_key), list):
                    data[last_key] = []
                data[last_key].append(parse_value(item.group(1)))
    return data, m.group(2).strip()


def main():
    if not os.path.isdir(BOTS_DIR):
        print(f"Pasta não encontrada: {BOTS_DIR}", file=sys.stderr)
        sys.exit(1)

    files = sorted(f for f in os.listdir(BOTS_DIR) if f.lower().endswith(".md"))

    # Se existir um manifest (index.json), respeita a ordem dele primeiro.
    manifest = os.path.join(BOTS_DIR, "index.json")
    if os.path.isfile(manifest):
        try:
            with open(manifest, encoding="utf-8") as fh:
                order = [f for f in json.load(fh) if f in files]
            files = order + [f for f in files if f not in order]
        except Exception as e:
            print(f"Aviso: index.json ignorado ({e})", file=sys.stderr)

    bots, skipped = [], []
    for fname in files:
        path = os.path.join(BOTS_DIR, fname)
        with open(path, encoding="utf-8") as fh:
            data, _ = parse_frontmatter(fh.read())
        name = str(data.get("name", "")).strip()
        username = str(data.get("username", "")).strip().lstrip("@")
        if not name or not username:
            skipped.append(fname)
            continue
        color = data.get("color")
        bots.append({
            "name": name,
            "username": username,
            "description": str(data.get("description", "")),
            "stats": str(data.get("stats", "")),
            "image": resolve_image_path(str(data.get("image", "")) or None),
            "color": color if isinstance(color, list) and len(color) >= 2 else ["#5B8DEF", "#3E63C9"],
            "tags": [str(t) for t in data.get("tags", [])] if isinstance(data.get("tags"), list) else [],
            "featured": data.get("featured") is True,
        })

    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(bots, fh, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUT_FILE) / 1024
    print(f"OK: {len(bots)} bots -> {OUT_FILE} ({size_kb:.1f} KB)")
    if skipped:
        print(f"Ignorados (sem name/username): {', '.join(skipped)}", file=sys.stderr)


if __name__ == "__main__":
    main()
