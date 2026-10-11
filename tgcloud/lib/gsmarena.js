import { fetch } from 'sdk';

/**
 * Searches GSMArena for mobile devices without using an API key.
 * @param {string} query Search keyword
 * @returns {Promise<Array<{id: string, title: string, pageUrl: string, imgUrl: string, brand: string, model: string}>>}
 */
export async function searchGSMArena(query) {
  const q = (query || '').trim();
  if (!q) {
    return [];
  }

  const searchUrl = `https://m.gsmarena.com/results.php3?sName=${encodeURIComponent(q)}`;

  try {
    const res = await fetch(searchUrl, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
      },
    });

    if (!res.ok) {
      console.warn('GSMArena fetch non-ok status:', res.status);
      return [];
    }

    const html = await res.text();
    const regex = /<li><a href=([^>]+)><img src=([^ ]+) title="([^"]+)"><strong>([^<]+)<br>([^<]+)<\/strong><\/a><\/li>/g;

    const results = [];
    let match;
    let index = 1;

    while ((match = regex.exec(html)) !== null) {
      const rawHref = match[1].replace(/['"]/g, '');
      const rawImg = match[2].replace(/['"]/g, '');
      const title = match[3].trim();
      const brand = match[4].trim();
      const model = match[5].trim();

      const pageUrl = rawHref.startsWith('http')
        ? rawHref
        : rawHref.startsWith('//')
        ? `https:${rawHref}`
        : `https://www.gsmarena.com/${rawHref.replace(/^\//, '')}`;

      const imgUrl = rawImg.startsWith('http')
        ? rawImg
        : rawImg.startsWith('//')
        ? `https:${rawImg}`
        : `https://www.gsmarena.com/${rawImg.replace(/^\//, '')}`;

      // Extract device ID slug or unique identifier from href if possible
      const idMatch = rawHref.match(/([a-zA-Z0-9_]+-\d+\.php)/);
      const id = idMatch ? idMatch[1] : `gsm_${index}`;

      results.push({
        id,
        title,
        pageUrl,
        imgUrl,
        brand,
        model,
      });

      index++;
    }

    return results;
  } catch (err) {
    console.error('Error fetching GSMArena search results:', err);
    return [];
  }
}
