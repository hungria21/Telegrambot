# Bot Telegram Serverless — MyAnimeList Inline Query Handler

Este projeto implementa um handler de `inline_query` para o [Telegram Serverless](https://core.telegram.org/bots/serverless), utilizando a API do MyAnimeList (via Jikan API v4).

## Estrutura do Projeto

```text
tgcloud/
├── handlers/
│   └── inline_query.js   # Trata os eventos de busca inline do Telegram
└── lib/
    └── mal.js            # Módulo auxiliar de integração com a API do MyAnimeList
```

## Como Funciona

1. Quando o usuário digita `@SeuBot nome_do_anime` em qualquer chat no Telegram, o Telegram envia uma atualização `inline_query` para o bot.
2. O handler `tgcloud/handlers/inline_query.js` recebe o evento e invoca a função `searchAnime` do módulo `tgcloud/lib/mal.js`.
3. A função faz uma requisição HTTP para a API do MyAnimeList (`https://api.jikan.moe/v4/anime?q=...`) usando o `fetch` nativo da SDK (`import { fetch } from 'sdk'`).
4. Os resultados são formatados como artigos inline (`InlineQueryResultArticle`) contendo título, imagem de capa, sinopse, pontuação e botão com link direto para o MyAnimeList.
5. O bot responde ao Telegram utilizando `api.answerInlineQuery`.

## Como Testar Localmente

Você pode testar a execução do handler com a CLI `tgcloud`:

```bash
# Testar com uma busca vazia (exibe instrução de ajuda)
npx tgcloud run handlers/inline_query '{ id: "123", query: "" }'

# Testar buscando um anime específico
npx tgcloud run handlers/inline_query '{ id: "123", query: "Naruto" }'
```

## Como Fazer Deploy

1. Garanta que o recurso Serverless esteja ativado no [@BotFather](https://t.me/BotFather) (`Bot Settings -> Serverless`).
2. Faça login com o token CLI fornecido pelo BotFather:
   ```bash
   npx tgcloud login
   ```
3. Envie o código para o Telegram Serverless:
   ```bash
   npx tgcloud push
   ```
4. Sincronize o webhook para garantir que `inline_query` receba atualizações:
   ```bash
   npx tgcloud webhook sync
   ```
