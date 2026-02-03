/**
 * 豆瓣热搜 - TVBox QuickJS Plugin
 * 功能：展示豆瓣热门影视，点击自动进入搜索
 * 不提供播放，只解决"看什么"的问题
 * 
 * 更新：使用豆瓣官方 API
 */

const DOUBAN_BASE = 'https://movie.douban.com';
const SEARCH_API = `${DOUBAN_BASE}/j/search_subjects`;
const SUBJECT_API = `${DOUBAN_BASE}/j/subject_abstract`;

const headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://movie.douban.com/'
};

/**
 * 初始化
 */
async function init(cfg) {
    console.log('豆瓣热搜插件初始化');
}

/**
 * 首页分类
 */
async function home(filter) {
    const classes = [
        { type_id: '热门', type_name: '热门' },
        { type_id: '最新', type_name: '最新' },
        { type_id: '经典', type_name: '经典' },
        { type_id: '豆瓣高分', type_name: '豆瓣高分' },
        { type_id: '冷门佳片', type_name: '冷门佳片' },
        { type_id: '华语', type_name: '华语' },
        { type_id: '欧美', type_name: '欧美' },
        { type_id: '韩国', type_name: '韩国' },
        { type_id: '日本', type_name: '日本' }
    ];

    return JSON.stringify({
        class: classes,
        filters: {}
    });
}

/**
 * 首页推荐 - 显示热门
 */
async function homeVod() {
    return category('热门', 1, false, {});
}

/**
 * 分类列表
 */
async function category(tid, pg, filter, extend) {
    try {
        const page_start = (parseInt(pg) - 1) * 20;
        const url = `${SEARCH_API}?type=movie&tag=${encodeURIComponent(tid)}&page_limit=20&page_start=${page_start}`;
        
        console.log('请求URL: ' + url);
        
        const r = await req(url, { headers });
        const data = JSON.parse(r.content);
        
        let videos = [];
        const subjects = data.subjects || [];
        
        console.log('找到 ' + subjects.length + ' 个影片');
        
        for (let i = 0; i < subjects.length; i++) {
            const item = subjects[i];
            
            const title = item.title || '';
            const rate = item.rate || '0';
            const cover = item.cover || '';
            const id = item.id || '';
            const url = item.url || '';
            
            // 构建备注信息
            let remarks = '';
            if (rate && rate !== '0') {
                remarks = `⭐${rate}`;
            }
            
            if (title) {
                videos.push({
                    vod_id: `search:${title}`,  // 使用 search: 前缀标记为搜索
                    vod_name: title,
                    vod_pic: cover,
                    vod_remarks: remarks,
                    vod_year: '',
                    vod_area: '',
                    vod_actor: '',
                    vod_director: '',
                    vod_content: `豆瓣评分: ${rate}\n豆瓣ID: ${id}\n\n点击将自动搜索该影片`
                });
            }
        }
        
        console.log(`返回 ${videos.length} 个影片`);
        
        return JSON.stringify({
            page: parseInt(pg),
            pagecount: 10,  // 豆瓣搜索支持多页
            limit: 20,
            total: videos.length,
            list: videos
        });
        
    } catch (e) {
        console.log('category出错: ' + e);
        return JSON.stringify({
            page: parseInt(pg),
            pagecount: 1,
            limit: 20,
            total: 0,
            list: []
        });
    }
}

/**
 * 详情页 - 返回搜索提示
 */
async function detail(id) {
    try {
        // 如果是搜索标记，提取真实片名
        let searchName = id;
        if (id.startsWith('search:')) {
            searchName = id.substring(7);
        }
        
        // 返回一个特殊的详情页，提示用户进行搜索
        // 使用 msearch:// 协议尝试触发搜索
        const vod = {
            vod_id: id,
            vod_name: searchName,
            vod_pic: '',
            vod_remarks: '点击播放自动搜索',
            vod_content: `这是豆瓣热搜推荐的影片。\n\n点击下方"自动搜索"按钮，将自动跳转到搜索界面搜索"${searchName}"。\n\n豆瓣热搜不提供播放源，只帮你发现好片。`,
            vod_play_from: '自动搜索',
            vod_play_url: `自动搜索${searchName}$msearch:${searchName}`
        };
        
        return JSON.stringify({ list: [vod] });
        
    } catch (e) {
        console.log('detail出错: ' + e);
        return JSON.stringify({ list: [] });
    }
}

/**
 * 搜索 - 使用豆瓣搜索API
 */
async function search(wd, quick) {
    try {
        const url = `${SEARCH_API}?type=movie&tag=${encodeURIComponent(wd)}&page_limit=20&page_start=0`;
        console.log('搜索URL: ' + url);
        
        const r = await req(url, { headers });
        const data = JSON.parse(r.content);
        
        let videos = [];
        const subjects = data.subjects || [];
        
        for (let i = 0; i < subjects.length; i++) {
            const item = subjects[i];
            
            const title = item.title || '';
            const rate = item.rate || '0';
            const cover = item.cover || '';
            const id = item.id || '';
            
            let remarks = '';
            if (rate && rate !== '0') {
                remarks = `⭐${rate}`;
            }
            
            if (title) {
                videos.push({
                    vod_id: `search:${title}`,
                    vod_name: title,
                    vod_pic: cover,
                    vod_remarks: remarks,
                    vod_year: '',
                    vod_actor: '',
                    vod_content: `豆瓣评分: ${rate}\n豆瓣ID: ${id}\n\n点击将自动搜索该影片`
                });
            }
        }
        
        console.log(`搜索到 ${videos.length} 个结果`);
        
        return JSON.stringify({
            page: 1,
            pagecount: 1,
            limit: 20,
            total: videos.length,
            list: videos
        });
        
    } catch (e) {
        console.log('search出错: ' + e);
        return JSON.stringify({
            page: 1,
            pagecount: 1,
            limit: 20,
            total: 0,
            list: []
        });
    }
}

/**
 * 播放解析 - 尝试触发搜索
 */
async function play(flag, id, flags) {
    try {
        // 如果 URL 以 msearch: 开头，尝试触发搜索
        if (id.startsWith('msearch:')) {
            const searchKeyword = id.substring(8);
            console.log('尝试触发搜索: ' + searchKeyword);
            
            // 返回特殊格式，尝试让 TVBox 识别为搜索请求
            return JSON.stringify({
                parse: 0,
                url: id,  // 保持 msearch: 协议
                header: {},
                jx: 0
            });
        }
        
        // 豆瓣热搜不提供播放功能
        return JSON.stringify({
            parse: 0,
            url: '',
            header: {}
        });
    } catch (e) {
        console.log('play出错: ' + e);
        return JSON.stringify({
            parse: 0,
            url: ''
        });
    }
}

// 导出接口
export default {
    init,
    home,
    homeVod,
    category,
    detail,
    search,
    play
};
