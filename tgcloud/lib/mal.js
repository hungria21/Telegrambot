import { fetch } from 'sdk';

/**
 * Busca animes na API MyAnimeList (via Jikan API v4).
 * @param {string} query Termo de busca fornecido pelo usuário.
 * @param {number} limit Quantidade máxima de resultados (padrão: 10).
 * @returns {Promise<Array>} Lista de resultados formatados em InlineQueryResultArticle.
 */
export async function searchAnime(query, limit = 10) {
  const q = query.trim();
  if (!q) {
    return [];
  }

  const url = `https://api.jikan.moe/v4/anime?q=${encodeURIComponent(q)}&limit=${limit}`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('Erro na resposta do Jikan API:', response.status, response.statusText);
      return [];
    }

    const data = await response.json();
    const items = data.data || [];

    return items.map((anime) => {
      const title = anime.title || anime.title_english || 'Sem título';
      const score = anime.score ? `⭐ ${anime.score}` : 'Sem nota';
      const episodes = anime.episodes ? `${anime.episodes} eps` : 'Status: ' + (anime.status || 'Desconhecido');
      const type = anime.type || 'Anime';
      const year = anime.year || (anime.aired?.prop?.from?.year) || '';
      const yearText = year ? ` (${year})` : '';

      const imageUrl = anime.images?.jpg?.large_image_url || anime.images?.jpg?.image_url;
      const thumbUrl = anime.images?.jpg?.small_image_url || anime.images?.jpg?.image_url;
      const malUrl = anime.url || `https://myanimelist.net/anime/${anime.mal_id}`;

      const synopsis = anime.synopsis
        ? (anime.synopsis.length > 200 ? anime.synopsis.slice(0, 197) + '...' : anime.synopsis)
        : 'Sem sinopse disponível.';

      const description = `${type}${yearText} • ${score} • ${episodes}`;

      let messageText = `🍿 <b><a href="${malUrl}">${escapeHtml(title)}</a></b>\n`;
      messageText += `<b>Tipo:</b> ${escapeHtml(type)}${yearText}\n`;
      messageText += `<b>Nota:</b> ${score}\n`;
      messageText += `<b>Episódios:</b> ${escapeHtml(episodes)}\n\n`;
      messageText += `📝 <b>Sinopse:</b>\n${escapeHtml(anime.synopsis || 'Sem sinopse.')}`;

      return {
        type: 'article',
        id: `mal_anime_${anime.mal_id}`,
        title: title,
        description: description,
        thumbnail_url: thumbUrl,
        input_message_content: {
          message_text: messageText,
          parse_mode: 'HTML',
          disable_web_page_preview: false,
        },
        reply_markup: {
          inline_keyboard: [
            [
              {
                text: '🌐 Ver no MyAnimeList',
                url: malUrl,
              },
            ],
          ],
        },
      };
    });
  } catch (error) {
    console.error('Erro ao buscar animes no MyAnimeList:', error);
    return [];
  }
}

/**
 * Escapa caracteres especiais de HTML para evitar quebras no parse_mode do Telegram.
 * @param {string} text
 * @returns {string}
 */
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
