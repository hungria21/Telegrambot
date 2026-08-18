"""
upload_para_github.py
----------------------
Sobe em lote os arquivos gerados pelo exportar_bots.py (pasta site/) pro
repositório do GitHub, usando a API do GitHub direto (Git Data API).

Não precisa do binário "git" instalado — só da biblioteca "requests".
Funciona igual no Pydroid e no Termux.

  pip install requests

MAPEAMENTO DE PASTAS (local -> repositório):
  site/postagem/*.md (ou site/postagens/*.md) -> content/bots/*.md
  site/imagens/*.png                         -> images/bots/*.png
  site/index.json                            -> content/bots/index.json (mesclado)
  content/bots.json                          -> content/bots.json (gerado/atualizado)

O site agora utiliza um único arquivo `content/bots.json` compilado para exibir
todas as postagens em uma só requisição. Este script garante que o `bots.json`
seja atualizado e enviado ao repositório junto com as postagens e imagens.
"""

import base64
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

# ========== CONFIGURAÇÃO ==========
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "SEU_TOKEN_AQUI")   # Personal Access Token com escopo "repo"
OWNER = "hungria21"
REPO = "Telegrambot"
BRANCH = "main"

LOCAL_DIR = Path("/storage/emulated/0/Download/site")
if not LOCAL_DIR.exists():
    # Fallback se executado no diretório atual ou estrutura alternativa
    if Path("site").exists():
        LOCAL_DIR = Path("site")

INDEX_LOCAL = LOCAL_DIR / "index.json"

POSTS_REMOTE = "content/bots"
IMAGES_REMOTE = "images/bots"
INDEX_REMOTE = "content/bots/index.json"
BOTS_JSON_REMOTE = "content/bots.json"

STATE_FILE = Path("upload_state.json")
CHUNK_SIZE = 200          # quantos arquivos por commit
COMMIT_MESSAGE = "Adiciona lote de bots via upload_para_github.py"

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def find_posts_dir(base_dir: Path) -> Path:
    for name in ["postagem", "postagens", "posts"]:
        p = base_dir / name
        if p.exists() and p.is_dir():
            return p
    return base_dir / "postagem"


def find_images_dir(base_dir: Path) -> Path:
    for name in ["imagens", "images", "imgs"]:
        p = base_dir / name
        if p.exists() and p.is_dir():
            return p
    return base_dir / "imagens"


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


def extract_bot_dict(data):
    name = str(data.get("name", "")).strip()
    username = str(data.get("username", "")).strip().lstrip("@")
    if not name or not username:
        return None
    color = data.get("color")
    return {
        "name": name,
        "username": username,
        "description": str(data.get("description", "")),
        "stats": str(data.get("stats", "")),
        "image": str(data.get("image", "")) or None,
        "color": color if isinstance(color, list) and len(color) >= 2 else ["#5B8DEF", "#3E63C9"],
        "tags": [str(t) for t in data.get("tags", [])] if isinstance(data.get("tags"), list) else [],
        "featured": data.get("featured") is True,
    }


def load_state() -> set:
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_state(uploaded: set):
    STATE_FILE.write_text(
        json.dumps(sorted(uploaded), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def gh_get(url, **kwargs):
    r = requests.get(url, headers=HEADERS, **kwargs)
    r.raise_for_status()
    return r.json()


def gh_post(url, payload):
    r = requests.post(url, headers=HEADERS, json=payload)
    if not r.ok:
        print("ERRO:", r.status_code, r.text[:500])
        r.raise_for_status()
    return r.json()


def get_branch_ref():
    return gh_get(f"{API}/repos/{OWNER}/{REPO}/git/ref/heads/{BRANCH}")


def get_commit(sha):
    return gh_get(f"{API}/repos/{OWNER}/{REPO}/git/commits/{sha}")


def create_blob(content_bytes: bytes) -> str:
    payload = {
        "content": base64.b64encode(content_bytes).decode("ascii"),
        "encoding": "base64",
    }
    data = gh_post(f"{API}/repos/{OWNER}/{REPO}/git/blobs", payload)
    return data["sha"]


def get_remote_file(remote_path: str):
    try:
        data = gh_get(
            f"{API}/repos/{OWNER}/{REPO}/contents/{remote_path}",
            params={"ref": BRANCH},
        )
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
    except requests.HTTPError:
        return None


def get_remote_index() -> list:
    """Busca o index.json que já existe no repositório, se existir."""
    raw = get_remote_file(INDEX_REMOTE)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return []


def get_remote_bots_json() -> list:
    """Busca o bots.json compilado que já existe no repositório, se existir."""
    raw = get_remote_file(BOTS_JSON_REMOTE)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return []


def merge_index(remote_list: list, local_list: list) -> list:
    merged = list(remote_list)
    existing = set(remote_list)
    for item in local_list:
        if item not in existing:
            merged.append(item)
            existing.add(item)
    return merged


def build_tree_entries(files_to_upload):
    """files_to_upload: lista de tuplas (local_path, remote_path, is_binary)"""
    entries = []
    for local_path, remote_path, is_binary in files_to_upload:
        raw = local_path.read_bytes()
        if is_binary:
            blob_sha = create_blob(raw)
            entries.append(
                {"path": remote_path, "mode": "100644", "type": "blob", "sha": blob_sha}
            )
        else:
            entries.append(
                {
                    "path": remote_path,
                    "mode": "100644",
                    "type": "blob",
                    "content": raw.decode("utf-8"),
                }
            )
    return entries


def commit_chunk(files_to_upload, message, max_retries=5):
    """
    Monta a blob/tree a partir dos arquivos já lidos, e refaz a leitura
    da branch + PATCH do ref em caso de erro 422.
    """
    entries = build_tree_entries(files_to_upload)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            ref = get_branch_ref()
            base_commit_sha = ref["object"]["sha"]
            base_commit = get_commit(base_commit_sha)
            base_tree_sha = base_commit["tree"]["sha"]

            tree = gh_post(
                f"{API}/repos/{OWNER}/{REPO}/git/trees",
                {"base_tree": base_tree_sha, "tree": entries},
            )

            new_commit = gh_post(
                f"{API}/repos/{OWNER}/{REPO}/git/commits",
                {
                    "message": message,
                    "tree": tree["sha"],
                    "parents": [base_commit_sha],
                },
            )

            r = requests.patch(
                f"{API}/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}",
                headers=HEADERS,
                json={"sha": new_commit["sha"]},
            )
            r.raise_for_status()
            return  # sucesso

        except requests.HTTPError as e:
            last_error = e
            wait = attempt * 4
            print(f"  [aviso] falha ao commitar (tentativa {attempt}/{max_retries}): {e}")
            print(f"  Aguardando {wait}s e tentando de novo...")
            time.sleep(wait)

    raise last_error


def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def rebuild_bots_json(posts_dir: Path) -> list:
    """
    Compila localmente todos os posts de content/bots/ e da pasta local site/postagem
    combinados com o bots.json remoto.
    """
    bots_dict = {}

    # 1. Carrega o bots.json remoto se existir
    remote_bots = get_remote_bots_json()
    for b in remote_bots:
        if isinstance(b, dict) and "username" in b:
            bots_dict[b["username"].lower()] = b

    # 2. Se a pasta local content/bots existir (repositório clonado)
    repo_bots_dir = Path("content/bots")
    if repo_bots_dir.exists() and repo_bots_dir.is_dir():
        for md_path in repo_bots_dir.glob("*.md"):
            data, _ = parse_frontmatter(md_path.read_text(encoding="utf-8"))
            bot = extract_bot_dict(data)
            if bot:
                bots_dict[bot["username"].lower()] = bot

    # 3. Processa todos os posts locais da pasta site/postagem
    if posts_dir.exists():
        for md_path in posts_dir.glob("*.md"):
            data, _ = parse_frontmatter(md_path.read_text(encoding="utf-8"))
            bot = extract_bot_dict(data)
            if bot:
                bots_dict[bot["username"].lower()] = bot

    return list(bots_dict.values())


def main():
    posts_local = find_posts_dir(LOCAL_DIR)
    images_local = find_images_dir(LOCAL_DIR)

    uploaded = load_state()

    # monta a lista de todos os arquivos ainda não enviados
    pending = []
    if posts_local.exists():
        for md_path in sorted(posts_local.glob("*.md")):
            key = f"post:{md_path.name}"
            if key not in uploaded:
                pending.append((md_path, f"{POSTS_REMOTE}/{md_path.name}", False, key))

    if images_local.exists():
        for img_ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
            for img_path in sorted(images_local.glob(img_ext)):
                key = f"img:{img_path.name}"
                if key not in uploaded:
                    pending.append((img_path, f"{IMAGES_REMOTE}/{img_path.name}", True, key))

    if not pending:
        print("Nada novo para enviar nas postagens/imagens.")
    else:
        print(f"{len(pending)} arquivos pendentes. Enviando em lotes de {CHUNK_SIZE}...")

        for i, chunk in enumerate(chunked(pending, CHUNK_SIZE), start=1):
            files_to_upload = [(p, r, b) for (p, r, b, k) in chunk]
            print(f"Lote {i}: enviando {len(files_to_upload)} arquivo(s)...")

            commit_chunk(files_to_upload, f"{COMMIT_MESSAGE} ({len(files_to_upload)} arquivos)")

            for (_, _, _, key) in chunk:
                uploaded.add(key)
            save_state(uploaded)

            print(f"Lote {i} enviado com sucesso.")
            time.sleep(1)

    # Atualiza index.json se existir
    if INDEX_LOCAL.exists():
        try:
            local_index = json.loads(INDEX_LOCAL.read_text(encoding="utf-8"))
            remote_index = get_remote_index()
            merged_index = merge_index(remote_index, local_index)

            if merged_index != remote_index:
                print("Atualizando index.json no repositório...")
                index_content = json.dumps(merged_index, ensure_ascii=False, indent=2) + "\n"

                tmp_path = Path("_index_temp.json")
                tmp_path.write_text(index_content, encoding="utf-8")
                commit_chunk(
                    [(tmp_path, INDEX_REMOTE, False)],
                    "Atualiza index.json com novos bots",
                )
                tmp_path.unlink()
                print("index.json atualizado.")
        except Exception as e:
            print(f"Aviso ao processar index.json: {e}")

    # Atualiza o content/bots.json compilado para o site carregar em uma única requisição
    print("Atualizando content/bots.json no repositório...")
    try:
        # Se build.py existe no diretório atual, tenta executá-lo primeiro se houver content/bots
        if Path("build.py").exists() and Path("content/bots").exists():
            import subprocess
            subprocess.run([sys.executable, "build.py"], check=False)

        bots_list = rebuild_bots_json(posts_local)
        if bots_list:
            bots_json_content = json.dumps(bots_list, ensure_ascii=False, separators=(",", ":"))
            tmp_bots_path = Path("_bots_temp.json")
            tmp_bots_path.write_text(bots_json_content, encoding="utf-8")

            # Também salva localmente em content/bots.json se o diretório existir
            if Path("content").exists():
                Path("content/bots.json").write_text(bots_json_content, encoding="utf-8")

            commit_chunk(
                [(tmp_bots_path, BOTS_JSON_REMOTE, False)],
                "Atualiza content/bots.json para requisição única",
            )
            tmp_bots_path.unlink()
            print("content/bots.json atualizado com sucesso no GitHub!")
    except Exception as e:
        print(f"Erro ao atualizar content/bots.json: {e}")

    print("\nConcluído!")


if __name__ == "__main__":
    main()
