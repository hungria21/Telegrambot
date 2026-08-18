# BuscaBots — Diretório de bots do Telegram

Site estático (sem build de frontend, sem backend) pronto para hospedar no
**GitHub Pages**, otimizado para **milhares de bots**: o site faz **uma única
requisição** (`content/bots.json`), não importa quantas postagens existam.

## Estrutura

```
index.html                       Página principal
assets/css/style.css             Estilos (tema claro/escuro)
assets/js/app.js                 Lógica do app (busca, tema, paginação)
assets/js/i18n.js                Sistema de tradução
assets/js/markdown.js            Parser de frontmatter (modo fallback)
i18n/*.json                      Traduções (pt-BR, en, es)
content/bots/*.md                Um arquivo por bot (frontmatter + texto)
content/bots.json                Índice compilado (gerado automaticamente)
content/bots/index.json          (Opcional) ordem manual dos posts
images/bots/*.png                Imagens/ícones dos bots
build.py                         Compila os .md em bots.json
.github/workflows/build-bots.yml GitHub Action que roda o build.py no push
```

## Publicar no GitHub Pages

1. Suba todo o conteúdo desta pasta para a raiz do repositório.
2. Em **Settings → Pages**, selecione a branch `main` e a pasta `/ (root)`.
3. O arquivo `.nojekyll` já está incluído — não o apague.

## Adicionar um novo bot (postagem via .md)

1. Crie `content/bots/meu-bot.md`:

```markdown
---
name: Nome do Bot
username: usuario_do_bot        # sem @
description: Descrição curta que aparece no card.
stats: 10 mil usuários/mês      # opcional
image: images/bots/meu-bot.png  # opcional; sem imagem, usa iniciais + cor
color: ["#6C8DFF", "#3C57D6"]   # cor do avatar de fallback
tags: [busca, utilidades]       # usadas na busca
featured: true                  # true = aparece no topo ("Em alta")
---

Texto livre opcional (reservado para futura página de detalhes).
```

2. Coloque a imagem em `images/bots/meu-bot.png` (quadrada, ~256px).
3. **Commit e push — pronto.** A GitHub Action incluída
   (`.github/workflows/build-bots.yml`) regenera o `content/bots.json`
   automaticamente e commita no repositório.

Se preferir gerar localmente: rode `python3 build.py` antes do push.
Não é necessário editar lista nenhuma: o build varre todos os `.md` da pasta
(em ordem alfabética). Se quiser controlar a ordem, mantenha um
`content/bots/index.json` com os nomes dos arquivos na ordem desejada.

## Como o site escala para milhares de bots

- **1 requisição**: todos os dados vêm do `content/bots.json` compilado
  (~0,24 KB por bot → 3.000 bots ≈ 720 KB, menos que uma foto).
- **Renderização paginada**: apenas 40 cards são desenhados por vez; ao
  rolar, mais 40 são adicionados (rolagem infinita). 3.000 bots não travam
  a página.
- **Busca instantânea**: filtrada em memória por nome, @usuario, descrição
  e tags.
- **Fallback**: se `bots.json` não existir (ex.: testando sem rodar o
  build), o site usa `content/bots/index.json` e lê os `.md` um a um —
  serve só para desenvolvimento com poucos bots.

## Adicionar um novo idioma

1. Copie `i18n/pt-BR.json` para `i18n/<codigo>.json` e traduza os textos.
2. Em `assets/js/i18n.js`, adicione o código ao array `AVAILABLE`.
3. Em `assets/js/app.js`, adicione o rótulo em `LANG_LABELS`.

O idioma padrão é detectado pelo navegador do usuário e pode ser trocado em
**Configurações → Idioma** (a escolha fica salva no navegador).

## Tema

Claro/escuro em **Configurações → Tema**. Na primeira visita segue a
preferência do sistema do usuário; depois a escolha fica salva.
