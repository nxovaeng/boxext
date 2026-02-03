/**
 * 豆瓣热搜 v2 - TVBox QuickJS Plugin (takagen99)
 * 功能：展示豆瓣热门影视，提供评分和简介
 * 长按可使用快搜功能搜索其他站点
 */

const DOUBAN_BASE = 'https://movie.douban.com';
const SEARCH_API = `${DOUBAN_BASE}/j/search_subjects`;
const SUBJECT_API = `${DOUBAN_BASE}/j/subject_abstract`;

const headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://movie.douban.com/'
};

async function init(cfg) {
    console.log('豆瓣热搜v2插件初始化');
}

async function home(filter) {
    const classes = [
        { type_id: '热门', type_name: '🔥热门' },
        { type_id: '最新', type_name: '🆕最新' },
        { type_id: '经典', type_name: '🎬经典' },
        { type_id: '豆瓣高分', type_name: '⭐高分' },
        { type_id: '冷门佳片', type_name: '💎冷门' },
        { type_id: '华语', type_name: '🇨🇳华语' },
        { type_id: '欧美', type_name: '🇺🇸欧美' },
        { type_id: '韩国', type_name: '🇰🇷韩国' },
        { type_id: '日本', type_name: '🇯🇵日本' }
    ];

    return JSON.stringify({
        class: classes,
        filters: {}
    });
}

async function homeVod() {
    return category('热门', 1, false, {});
}

async function category(tid, pg, filter, extend) {
    try {
        const page_start = (parseInt(pg) - 1) * 20;
        const url = `${SEARCH_API}?type=movie&tag=${encodeURIComponent(tid)}&page_limit=20&page_start=${page_start}`;

        const r = await req(url, { headers });
        const data = JSON.parse(r.content);

        let videos = [];
        const subjects = data.subjects || [];

        for (let i = 0; i < subjects.length; i++) {
            const item = subjects[i];
            let title = item.title || '';
            const rate = item.rate || '0';
            const cover = item.cover || '';
            const id = item.id || '';

            // 清理片名：去掉年份后缀 (2025) 等
            title = title.replace(/\s*\(\d{4}\)\s*$/, '').trim();

            let remarks = rate && rate !== '0' ? `⭐${rate}` : '';

            if (title) {
                videos.push({
                    vod_id: id,  // 使用豆瓣ID
                    vod_name: title,
                    vod_pic: cover,
                    vod_remarks: remarks
                });
            }
        }

        return JSON.stringify({
            page: parseInt(pg),
            pagecount: 10,
            limit: 20,
            total: videos.length,
            list: videos
        });

    } catch (e) {
        console.log('category出错: ' + e);
        return JSON.stringify({ page: 1, pagecount: 1, list: [] });
    }
}

/**
 * 详情页 - 展示豆瓣评分和简介
 */
async function detail(id) {
    try {
        // 获取豆瓣影片详情
        const url = `${SUBJECT_API}?subject_id=${id}`;
        console.log('获取详情: ' + url);

        let title = '';
        let cover = '';
        let rate = '';
        let intro = '';
        let year = '';
        let actors = '';
        let directors = '';

        try {
            const r = await req(url, { headers });
            const data = JSON.parse(r.content);
            const subject = data.subject || {};

            title = subject.title || `影片${id}`;
            cover = subject.cover || '';
            rate = subject.rate || '';
            intro = subject.short_info || '';
            directors = subject.directors ? subject.directors.join(' / ') : '';
            actors = subject.actors ? subject.actors.join(' / ') : '';

        } catch (e) {
            console.log('获取详情失败: ' + e);
            title = `影片${id}`;
        }

        // 构建简介内容
        let content = '';
        if (rate) content += `⭐ 豆瓣评分: ${rate}\n\n`;
        if (directors) content += `🎬 导演: ${directors}\n\n`;
        if (actors) content += `👥 演员: ${actors}\n\n`;
        if (intro) content += `📖 简介: ${intro}\n\n`;
        content += `\n💡 提示: 长按海报可使用快搜功能搜索其他站点`;

        const vod = {
            vod_id: id,
            vod_name: title,
            vod_pic: cover,
            vod_remarks: rate ? `⭐${rate}` : '',
            vod_year: year,
            vod_actor: actors,
            vod_director: directors,
            vod_content: content,
            vod_play_from: '',
            vod_play_url: ''
        };

        return JSON.stringify({ list: [vod] });

    } catch (e) {
        console.log('detail出错: ' + e);
        return JSON.stringify({ list: [] });
    }
}

async function search(wd, quick) {
    try {
        const url = `${SEARCH_API}?type=movie&tag=${encodeURIComponent(wd)}&page_limit=20&page_start=0`;
        const r = await req(url, { headers });
        const data = JSON.parse(r.content);

        let videos = [];
        const subjects = data.subjects || [];

        for (const item of subjects) {
            let title = item.title || '';
            const rate = item.rate || '0';
            const cover = item.cover || '';
            const id = item.id || '';

            // 清理片名：去掉年份后缀 (2025) 等
            title = title.replace(/\s*\(\d{4}\)\s*$/, '').trim();

            if (title) {
                videos.push({
                    vod_id: id,
                    vod_name: title,
                    vod_pic: cover,
                    vod_remarks: rate && rate !== '0' ? `⭐${rate}` : ''
                });
            }
        }

        return JSON.stringify({ page: 1, pagecount: 1, list: videos });

    } catch (e) {
        console.log('search出错: ' + e);
        return JSON.stringify({ page: 1, pagecount: 1, list: [] });
    }
}

async function play(flag, id, flags) {
    // 豆瓣热搜不提供播放源
    return JSON.stringify({ parse: 0, url: '' });
}

export default {
    init,
    home,
    homeVod,
    category,
    detail,
    search,
    play
};
