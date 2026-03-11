const { addonBuilder, serveHTTP } = require('stremio-addon-sdk');
const scraper = require('./scraper');

const PORT = 7000;

// ============================================================================
// Manifest
// ============================================================================

const manifest = {
    id: 'community.pipishi',
    version: '1.0.0',
    name: '皮皮狮 PiPiShi',
    description: '皮皮狮影视 — 电影、剧集、综艺、动漫',
    logo: 'https://www.pipishi.fun/mxtheme/images/favicon.png',
    resources: ['catalog', 'meta', 'stream'],
    types: ['movie', 'series'],
    catalogs: scraper.SITE.catalogs.map(cat => ({
        type: cat.type,
        id: cat.id,
        name: cat.name,
        extra: [
            { name: 'skip', isRequired: false },
            { name: 'search', isRequired: false }
        ]
    })),
    idPrefixes: ['pipishi:'],
    behaviorHints: {
        adult: false,
        p2p: false
    }
};

const builder = new addonBuilder(manifest);

// ============================================================================
// Catalog Handler
// ============================================================================

builder.defineCatalogHandler(async ({ type, id, extra }) => {
    console.log(`\n[Addon] Catalog request: type=${type}, id=${id}, extra=`, extra);

    // Search
    if (extra && extra.search) {
        console.log(`[Addon] Search: "${extra.search}"`);
        try {
            const results = await scraper.searchPipishi(extra.search);
            const metas = results.map(r => ({
                id: r.id,
                type: r.type || type,
                name: r.title,
                poster: r.poster,
                posterShape: 'regular'
            }));
            return { metas };
        } catch (err) {
            console.error('[Addon] Search error:', err.message);
            return { metas: [] };
        }
    }

    // Browse catalog
    const catalog = scraper.SITE.catalogs.find(c => c.id === id);
    if (!catalog) {
        console.log('[Addon] Unknown catalog:', id);
        return { metas: [] };
    }

    const skip = extra && extra.skip ? parseInt(extra.skip, 10) : 0;

    try {
        const recent = await scraper.getRecent(catalog.typeId, skip);
        const metas = recent.map(r => ({
            id: r.id,
            type: catalog.type,
            name: r.title,
            poster: r.poster,
            posterShape: 'regular',
            description: r.remark || undefined
        }));

        return {
            metas,
            hasMore: metas.length >= 30
        };
    } catch (e) {
        console.error('[Addon] Catalog error:', e.message);
        return { metas: [] };
    }
});

// ============================================================================
// Meta Handler
// ============================================================================

builder.defineMetaHandler(async ({ type, id }) => {
    console.log(`\n[Addon] Meta request: type=${type}, id=${id}`);

    const { vodId } = scraper.parseId(id);
    try {
        const meta = await scraper.getMeta(vodId);
        if (meta) {
            return { meta };
        }
    } catch (e) {
        console.error('[Addon] Meta error:', e.message);
    }
    return { meta: null };
});

// ============================================================================
// Stream Handler
// ============================================================================

builder.defineStreamHandler(async ({ type, id }) => {
    console.log(`\n[Addon] Stream request: type=${type}, id=${id}`);

    const { vodId, episode } = scraper.parseId(id);
    try {
        const streams = await scraper.getStreams(vodId, episode);

        console.log(`[Addon] 🎬 Streams for ID: ${vodId}, Episode: ${episode}`);
        streams.forEach((stream, index) => {
            console.log(`  [${index + 1}] ${stream.name} — ${stream.description}`);
            console.log(`      URL: ${stream.url}`);
        });

        return { streams };
    } catch (e) {
        console.error('[Addon] Stream error:', e.message);
        return { streams: [] };
    }
});

// ============================================================================
// Start Server
// ============================================================================

serveHTTP(builder.getInterface(), { port: PORT });
console.log(`\n🚀 PiPiShi Stremio Addon running at: http://localhost:${PORT}/manifest.json`);
console.log(`📺 Add to Stremio: http://YOUR_IP:${PORT}/manifest.json\n`);
