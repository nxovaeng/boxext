const axios = require('axios');
const cheerio = require('cheerio');
const crypto = require('crypto');

// ============================================================================
// Site Configuration
// ============================================================================

const SITE = {
    id: 'pipishi',
    name: 'PiPiShi',
    mainUrl: 'https://www.pipishi.fun',
    catalogs: [
        { typeId: 1, id: 'pipishi_movies', name: '皮皮狮 电影', type: 'movie' },
        { typeId: 2, id: 'pipishi_series', name: '皮皮狮 剧集', type: 'series' },
        { typeId: 3, id: 'pipishi_variety', name: '皮皮狮 综艺', type: 'series' },
        { typeId: 4, id: 'pipishi_anime', name: '皮皮狮 动漫', type: 'series' }
    ]
};

let globalCookie = '';

const defaultHeaders = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
};

// ============================================================================
// Encryption for Anti-Bot Challenge 1
// ============================================================================

const JS_KEY = 'jZ#8C*d!2$';

function encrypt(txt, key) {
    let chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let nh = Math.floor(Math.random() * 64);
    let ch = chars.charAt(nh);
    let mdKey = crypto.createHash('md5').update(key + ch).digest('hex');
    mdKey = mdKey.substring(nh % 8, nh % 8 + (nh % 8 > 7 ? nh % 8 : nh % 8 + 17));
    txt = base64encode(txt);
    let tmp = '';
    let k = 0;
    for (let i = 0; i < txt.length; i++) {
        k = k == mdKey.length ? 0 : k;
        let charCode = txt.charCodeAt(i) ^ mdKey.charCodeAt(k++);
        tmp += String.fromCharCode(charCode);
    }
    return encodeURIComponent(ch + base64encode(tmp));
}

function base64encode(str) {
    return Buffer.from(str, 'utf8').toString('base64');
}

// ============================================================================
// Anti-Bot Bypass Fetch (handles both Challenge types)
// ============================================================================

async function fetchWithBypass(url) {
    try {
        const headers = { ...defaultHeaders };
        if (globalCookie) headers['Cookie'] = globalCookie;

        let res = await axios.get(url, { headers, validateStatus: () => true, timeout: 15000 });

        if (res.headers['set-cookie']) {
            globalCookie = res.headers['set-cookie'].map(c => c.split(';')[0]).join('; ');
        }

        if (res.status === 200 && res.data && res.data.includes('robot.php')) {
            console.log(`[PiPiShi] Anti-bot triggered for: ${url}`);

            // Challenge 1: math.random + MD5
            const staticMatch1 = res.data.match(/var\s+staticchars\s*=\s*'([^']+)'/);
            const tokenMatch1 = res.data.match(/var\s+token\s*=\s*'([^']+)'/);

            // Challenge 2: encrypt2 (staticchars + base64)
            const staticMatch2 = res.data.match(/var\s+staticchars\s*=\s*"([^"]+)"/);
            const tokenMatch2 = res.data.match(/var\s+token\s*=\s*encrypt\("([^"]+)"\);/);

            if (staticMatch1 && tokenMatch1 && res.data.includes('math.random')) {
                // Challenge 1
                const staticchars = staticMatch1[1];
                const token = tokenMatch1[1];
                const p = encrypt(staticchars, token);
                const verificationUrl = `${SITE.mainUrl}/static/js/robot.php?p=${p}&${token}=`;

                let verifyRes = await axios.get(verificationUrl, {
                    headers: { ...defaultHeaders, 'Cookie': globalCookie, 'Referer': url },
                    validateStatus: () => true
                });

                if (verifyRes.headers['set-cookie']) {
                    globalCookie = verifyRes.headers['set-cookie'].map(c => c.split(';')[0]).join('; ');
                }

                res = await axios.get(url, {
                    headers: { ...defaultHeaders, 'Cookie': globalCookie },
                    validateStatus: () => true
                });
                console.log('[PiPiShi] Challenge 1 solved');
            } else if (staticMatch2 && tokenMatch2) {
                // Challenge 2
                const tokenRaw = tokenMatch2[1];
                const staticchars = staticMatch2[1];

                const encrypt2 = (_str) => {
                    let encodechars = "";
                    for (let i = 0; i < _str.length; i++) {
                        let num0 = staticchars.indexOf(_str[i]);
                        let code = num0 === -1 ? _str[i] : staticchars[(num0 + 3) % 62];
                        let num1 = Math.floor(Math.random() * 62);
                        let num2 = Math.floor(Math.random() * 62);
                        encodechars += staticchars[num1] + code + staticchars[num2];
                    }
                    return Buffer.from(encodechars).toString('base64');
                };

                const value = encrypt2(url);
                const token = encrypt2(tokenRaw);
                const postData = `value=${encodeURIComponent(value)}&token=${encodeURIComponent(token)}`;

                let verifyRes = await axios.post(`${SITE.mainUrl}/robot.php`, postData, {
                    headers: {
                        ...defaultHeaders,
                        'Cookie': globalCookie,
                        'Referer': url,
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    validateStatus: () => true
                });

                if (verifyRes.headers['set-cookie']) {
                    globalCookie = verifyRes.headers['set-cookie'].map(c => c.split(';')[0]).join('; ');
                }

                res = await axios.get(url, {
                    headers: { ...defaultHeaders, 'Cookie': globalCookie },
                    validateStatus: () => true
                });
                console.log('[PiPiShi] Challenge 2 solved');
            }
        }
        return res.data;
    } catch (e) {
        console.error('[PiPiShi] Fetch error:', e.message);
        return null;
    }
}

// ============================================================================
// Stream URL Decryption (identical to dadaqu — same MacCMS engine)
// ============================================================================

function md5(str) {
    return crypto.createHash('md5').update(str).digest('hex');
}

function decode1(cipherStr) {
    const key = md5('test');
    const decoded1 = Buffer.from(cipherStr, 'base64').toString('binary');
    let code = '';
    for (let i = 0; i < decoded1.length; i++) {
        const k = i % key.length;
        code += String.fromCharCode(decoded1.charCodeAt(i) ^ key.charCodeAt(k));
    }
    return Buffer.from(code, 'base64').toString('utf8');
}

function decodeFinalStream(input) {
    const out = decode1(input);
    const parts = out.split('/');
    if (parts.length < 3) return null;
    try {
        const arr1 = JSON.parse(Buffer.from(parts[0], 'base64').toString('utf8'));
        const arr2 = JSON.parse(Buffer.from(parts[1], 'base64').toString('utf8'));
        const cipherUrl = Buffer.from(parts[2], 'base64').toString('utf8');

        let realUrl = '';
        for (let c of cipherUrl) {
            if (/^[a-zA-Z]$/.test(c)) {
                const idx = arr2.indexOf(c);
                if (idx !== -1) {
                    realUrl += arr1[idx];
                } else {
                    realUrl += c;
                }
            } else {
                realUrl += c;
            }
        }
        return realUrl;
    } catch (e) {
        return null;
    }
}

function decodeFinalStream2(input) {
    try {
        const decoded = Buffer.from(input, 'base64').toString('binary');
        const chars = 'PXhw7UT1B0a9kQDKZsjIASmOezxYG4CHo5Jyfg2b8FLpEvRr3WtVnlqMidu6cN';
        let res = '';
        for (let i = 1; i < decoded.length; i += 3) {
            const idx = chars.indexOf(decoded[i]);
            if (idx === -1) {
                res += decoded[i];
            } else {
                res += chars[(idx + 59) % 62];
            }
        }
        return res;
    } catch (e) {
        return null;
    }
}

// ============================================================================
// Catalog: Recent / Browse
// ============================================================================

async function getRecent(typeId, skip = 0) {
    const page = Math.floor(skip / 36) + 1;
    const listUrl = `${SITE.mainUrl}/list/${typeId}--------${page}---.html`;
    console.log(`[PiPiShi] Fetching catalog (page ${page}): ${listUrl}`);

    const html = await fetchWithBypass(listUrl);
    if (!html) return [];

    const results = [];
    const $ = cheerio.load(html);

    // PiPiShi mxtheme layout: <a class="module-poster-item module-item">
    $('a.module-poster-item, a.module-item').each((i, el) => {
        const link = $(el).attr('href');
        const title = $(el).attr('title');
        let img = $(el).find('img').attr('data-original') || $(el).find('img').attr('data-src');

        const idMatch = link ? link.match(/\/vod\/(\d+)\.html/) : null;
        const vodId = idMatch ? idMatch[1] : null;

        if (vodId && title && !results.find(r => r.vodId === vodId)) {
            const remark = $(el).find('.module-item-note').text().trim();
            results.push({
                id: `${SITE.id}:${vodId}`,
                vodId,
                title,
                poster: img ? (img.startsWith('http') ? img : `${SITE.mainUrl}${img}`) : null,
                remark
            });
        }
    });

    console.log(`[PiPiShi] Found ${results.length} items on page ${page}`);
    return results;
}

// ============================================================================
// Search
// ============================================================================

async function searchPipishi(query) {
    if (!query) return [];
    console.log(`[PiPiShi] Searching for: "${query}"`);
    const searchUrl = `${SITE.mainUrl}/search/${encodeURIComponent(query)}-------------.html`;
    const html = await fetchWithBypass(searchUrl);
    if (!html) return [];

    const results = [];
    const $ = cheerio.load(html);

    // Search results: module-card-item or module-search-item or module-poster-item
    $('a.module-poster-item, a.module-item, .module-card-item').each((i, el) => {
        let link, title, img;

        if ($(el).is('a')) {
            link = $(el).attr('href');
            title = $(el).attr('title');
            img = $(el).find('img').attr('data-original') || $(el).find('img').attr('data-src');
        } else {
            const titleEl = $(el).find('.module-card-item-title a, a');
            title = titleEl.text().trim() || titleEl.attr('title');
            link = titleEl.attr('href');
            img = $(el).find('img').attr('data-original') || $(el).find('img').attr('data-src');
        }

        const idMatch = link ? link.match(/\/vod\/(\d+)\.html/) : null;
        const vodId = idMatch ? idMatch[1] : null;

        // Try to detect type
        const typeClass = $(el).find('.module-card-item-class, .module-item-note').text().trim();
        let type = 'series';
        if (typeClass === '电影' || typeClass === '正片') type = 'movie';

        if (vodId && title) {
            results.push({
                id: `${SITE.id}:${vodId}`,
                vodId,
                title,
                poster: img ? (img.startsWith('http') ? img : `${SITE.mainUrl}${img}`) : null,
                type
            });
        }
    });

    console.log(`[PiPiShi] Found ${results.length} search results`);
    return results;
}

// ============================================================================
// Meta (Detail Page)
// ============================================================================

async function getMeta(vodId) {
    const detailUrl = `${SITE.mainUrl}/vod/${vodId}.html`;
    console.log(`[PiPiShi] Fetching meta: ${detailUrl}`);
    const html = await fetchWithBypass(detailUrl);
    if (!html) return null;

    const $ = cheerio.load(html);
    const title = $('h1').text().trim();
    let img = $('.module-item-pic img').attr('data-original') || $('.module-item-pic img').attr('data-src');
    const poster = img ? (img.startsWith('http') ? img : `${SITE.mainUrl}${img}`) : null;
    const description = $('.module-info-introduction-content p, .module-info-introduction-content').text().trim();

    // Extract episodes
    const episodes = [];
    const firstList = $('.module-list').first();
    firstList.find('a').each((i, el) => {
        const link = $(el).attr('href');
        const epTitle = $(el).text().trim();
        const match = link ? link.match(/\/play\/(\d+)-(\d+)-(\d+)\.html/) : null;
        if (match) {
            const epNum = parseInt(match[3], 10);
            if (!episodes.find(e => e.episode === epNum)) {
                episodes.push({
                    id: `${SITE.id}:${match[1]}:${epNum}`,
                    title: epTitle,
                    episode: epNum,
                    season: 1
                });
            }
        }
    });

    const isSeries = episodes.length > 1 || (episodes.length === 1 && episodes[0].title.includes('集'));

    // Season grouping for long series
    if (isSeries && episodes.length > 20) {
        episodes.forEach(ep => {
            ep.season = Math.ceil(ep.episode / 20);
        });
    }

    return {
        id: `${SITE.id}:${vodId}`,
        type: isSeries ? 'series' : 'movie',
        name: title,
        poster,
        posterShape: 'regular',
        description,
        videos: isSeries ? episodes : undefined,
        background: poster
    };
}

// ============================================================================
// Streams (Play Page → API → Decode)
// ============================================================================

async function getStreams(vodId, episode = 1) {
    const detailUrl = `${SITE.mainUrl}/vod/${vodId}.html`;
    const html = await fetchWithBypass(detailUrl);
    if (!html) return [];

    const $ = cheerio.load(html);

    // Collect source names
    const sourceNames = [];
    $('.module-tab-items-box .tab-item, .module-tab-item').each((i, el) => {
        sourceNames.push($(el).attr('data-dropdown-value') || $(el).text().replace(/\d+$/, '').trim());
    });

    // Collect play links for the requested episode
    const playLinks = [];
    $('.module-list, .module-play-list').each((sourceIndex, listEl) => {
        const sourceName = sourceNames[sourceIndex] || `线路 ${sourceIndex + 1}`;
        $(listEl).find('a').each((i, el) => {
            const link = $(el).attr('href');
            const resolution = $(el).text().trim();
            const match = link ? link.match(/\/play\/(\d+)-(\d+)-(\d+)\.html/) : null;
            if (match && parseInt(match[3], 10) === parseInt(episode, 10)) {
                playLinks.push({ link, sourceName, resolution });
            }
        });
    });

    console.log(`[PiPiShi] Found ${playLinks.length} play links for episode ${episode}`);

    // Extract streams in parallel with timeout
    const EXTRACT_TIMEOUT = 15000;
    const extractPromises = playLinks.map(async (item) => {
        try {
            const playUrl = `${SITE.mainUrl}${item.link}`;
            const timeoutPromise = new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Extract timeout')), EXTRACT_TIMEOUT)
            );

            const extractPromise = (async () => {
                const playHtml = await fetchWithBypass(playUrl);
                if (!playHtml) return null;

                const playerMatch = playHtml.match(/var player_aaaa=({.*?})<\/script>/);
                if (!playerMatch) return null;

                const playerData = JSON.parse(playerMatch[1]);
                if (!playerData.url) return null;

                // Post to PiPiShi's play API
                const apiUrl = `${SITE.mainUrl}/lionplay/api.php`;
                const apiRes = await axios.post(apiUrl, `vid=${encodeURIComponent(playerData.url)}`, {
                    headers: {
                        ...defaultHeaders,
                        'Cookie': globalCookie,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Origin': SITE.mainUrl,
                        'Referer': `${SITE.mainUrl}/lionplay/index.php?vid=${playerData.url}`
                    },
                    validateStatus: () => true,
                    timeout: 10000
                });

                if (apiRes.status === 200 && apiRes.data && apiRes.data.data) {
                    const streamData = apiRes.data.data;
                    let streamUrl = '';

                    if (streamData.urlmode === 1) {
                        streamUrl = decodeFinalStream(streamData.url);
                    } else if (streamData.urlmode === 2) {
                        streamUrl = decodeFinalStream2(streamData.url);
                    } else if (streamData.url && streamData.url.startsWith('http')) {
                        streamUrl = streamData.url;
                    }

                    if (streamUrl && !streamUrl.includes('404.mp4')) {
                        return {
                            name: item.resolution || '标清',
                            description: `线路: ${item.sourceName}`,
                            url: streamUrl,
                            behaviorHints: {
                                notWebReady: true,
                                proxyHeaders: {
                                    request: {
                                        'User-Agent': defaultHeaders['User-Agent'],
                                        'Referer': `${SITE.mainUrl}/lionplay/index.php?vid=${playerData.url}`,
                                        'Origin': SITE.mainUrl
                                    }
                                }
                            }
                        };
                    }
                }
                return null;
            })();

            return await Promise.race([extractPromise, timeoutPromise]);
        } catch (e) {
            console.error('[PiPiShi] Stream extract error:', item.link, e.message);
            return null;
        }
    });

    const results = await Promise.all(extractPromises);
    const streams = results.filter(s => s !== null);
    console.log(`[PiPiShi] Resolved ${streams.length} valid streams`);
    return streams;
}

// ============================================================================
// ID Helpers
// ============================================================================

function parseId(stremioId) {
    const parts = stremioId.split(':');
    return {
        siteId: parts[0],
        vodId: parts[1],
        episode: parts[2] || 1
    };
}

// ============================================================================
// Exports
// ============================================================================

module.exports = {
    SITE,
    fetchWithBypass,
    getRecent,
    searchPipishi,
    getMeta,
    getStreams,
    parseId
};
