import { api } from 'sdk';
import { searchGSMArena } from '../lib/gsmarena.js';

/**
 * Telegram Serverless update handler for inline queries.
 * Handles update type: inline_query
 *
 * @param {import('telegram-typings').InlineQuery} inlineQuery The Telegram inline query update object
 */
export default async function (inlineQuery) {
  const query = (inlineQuery.query || '').trim();

  // If query is empty, answer with empty results or prompt
  if (!query) {
    await api.answerInlineQuery({
      inline_query_id: inlineQuery.id,
      results: [],
      cache_time: 300,
      switch_pm_text: 'Digite o nome do aparelho para buscar no GSMArena...',
      switch_pm_parameter: 'start',
    });
    return;
  }

  // Fetch search results from GSMArena
  const devices = await searchGSMArena(query);

  // Map search results into Telegram InlineQueryResultArticle objects (max 50)
  const results = devices.slice(0, 50).map((device) => {
    const titleEscaped = escapeMarkdown(device.title);
    const brandEscaped = escapeMarkdown(device.brand);
    const modelEscaped = escapeMarkdown(device.model);

    return {
      type: 'article',
      id: device.id,
      title: device.title,
      description: `${device.brand} - ${device.model}`,
      thumbnail_url: device.imgUrl,
      input_message_content: {
        message_text: `📱 *${titleEscaped}*\n\nMarca: ${brandEscaped}\nModelo: ${modelEscaped}\n\n🔗 [Ver no GSMArena](${device.pageUrl})`,
        parse_mode: 'Markdown',
        disable_web_page_preview: false,
      },
      reply_markup: {
        inline_keyboard: [
          [
            {
              text: '🌐 Abrir no GSMArena',
              url: device.pageUrl,
            },
          ],
        ],
      },
    };
  });

  await api.answerInlineQuery({
    inline_query_id: inlineQuery.id,
    results,
    cache_time: 300,
    is_personal: false,
  });
}

function escapeMarkdown(text) {
  return (text || '').replace(/[_*`\[]/g, '\\$&');
}
