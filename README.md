# BuscaBots — Diretório de bots do Telegram

Site estático (sem build, sem backend) pronto para hospedar no **GitHub Pages**.

## Estrutura

```
index.html              Página principal
assets/css/style.css    Estilos (tema claro/escuro)
assets/js/app.js        Lógica do app (busca, tema, sheet)
assets/js/i18n.js       Sistema de tradução
assets/js/markdown.js   Parser de frontmatter dos posts
i18n/pt-BR.json         Tradução português
i18n/en.json            Tradução inglês
i18n/es.json            Tradução espanhol
content/bots/index.json Manifest: lista dos posts (.md) exibidos
content/bots/*.md       Um arquivo por bot (frontmatter + texto)
images/bots/*.png       Imagens/ícones dos bots (hospedadas no repo)
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

2. Coloque a imagem em `images/bots/meu-bot.png` (quadrada, ~256px, PNG ou JPG).
3. Adicione `"meu-bot.md"` ao array em `content/bots/index.json`.
4. Commit e push — o GitHub Pages atualiza sozinho.

## Adicionar um novo idioma

1. Copie `i18n/pt-BR.json` para `i18n/<codigo>.json` e traduza os textos.
2. Em `assets/js/i18n.js`, adicione o código ao array `AVAILABLE`.
3. Em `assets/js/app.js`, adicione o rótulo em `LANG_LABELS`.

O idioma padrão é detectado pelo navegador do usuário e pode ser trocado em
**Configurações → Idioma** (a escolha fica salva no navegador).

## Tema

Claro/escuro em **Configurações → Tema**. Na primeira visita segue a
preferência do sistema do usuário; depois a escolha fica salva.
