import { api } from 'sdk';
import { searchAnime } from '../lib/mal.js';

/**
 * Handler de inline_query para o Telegram Serverless.
 * O Telegram envia o payload InlineQuery contendo `id`, `query`, `from`, `offset`, etc.
 *
 * @param {Object} inlineQuery Payload do evento inline_query enviado pelo Telegram.
 * @param {Object} ctx Contexto da execução.
 */
export default async function (inlineQuery, ctx) {
  const query = inlineQuery?.query || '';
  const inlineQueryId = inlineQuery?.id;

  if (!inlineQueryId) {
    console.warn('Recebido inline_query sem ID válido.');
    return;
  }

  // Se o usuário não digitou nada ou apenas espaços, retornamos uma dica de ajuda
  if (!query.trim()) {
    await api.answerInlineQuery({
      inline_query_id: inlineQueryId,
      results: [
        {
          type: 'article',
          id: 'help_search_mal',
          title: '🔍 Busque um anime no MyAnimeList',
          description: 'Digite o nome do anime após o nome do bot (ex: @botname Naruto)',
          input_message_content: {
            message_text: '💡 <b>Como usar a busca do MyAnimeList:</b>\nDigite <code>@seu_bot nome_do_anime</code> em qualquer chat para pesquisar animes diretamente!',
            parse_mode: 'HTML',
          },
        },
      ],
      cache_time: 300,
      is_personal: true,
    });
    return;
  }

  // Realiza a busca na API do MyAnimeList via lib/mal.js
  const results = await searchAnime(query, 10);

  // Envia a resposta da inline query de volta para o Telegram
  await api.answerInlineQuery({
    inline_query_id: inlineQueryId,
    results: results,
    cache_time: 300, // Cache de 5 minutos
    is_personal: false,
  });
}
