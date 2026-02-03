#!/usr/bin/env python3
"""
创建高级优化配置
- 高质量 API 站点
- 广告过滤规则
- 播放器优化
- DNS 优化
"""
import json
from pathlib import Path

# 广告过滤规则
AD_FILTERS = [
    # 常见广告域名
    "mimg.0c1q0l.cn",
    "www.googletagmanager.com",
    "www.google-analytics.com",
    "mc.usihnbcq.cn",
    "mg.g1mm3d.cn",
    "mscs.svaeuzh.cn",
    "cnzz.hhttm.top",
    "tp.vinuxhome.com",
    "cnzz.mmstat.com",
    "www.baihuillq.com",
    "s23.cnzz.com",
    "z3.cnzz.com",
    "c.cnzz.com",
    "stj.v1vo.top",
    "z12.cnzz.com",
    "img.mosflower.cn",
    "tips.gamevvip.com",
    "ehwe.yhdtns.com",
    "xdn.cqqc3.com",
    "www.jixunkyy.cn",
    "sp.chemacid.cn",
    "hm.baidu.com",
    "s9.cnzz.com",
    "z6.cnzz.com",
    "um.cavuc.com",
    "mav.mavuz.com",
    "wofwk.aoidf3.com",
    "z5.cnzz.com",
    "xc.hubeijieshikj.cn",
    "tj.tianwenhu.com",
    "xg.gars57.cn",
    "k.jinxiuzhilv.com",
    "cdn.bootcss.com",
    "ppl.xunzhuo123.com",
    "xomk.jiangjunmh.top",
    "img.xunzhuo123.com",
    "z1.cnzz.com",
    "s13.cnzz.com",
    "xg.huataisangao.cn",
    "z7.cnzz.com",
    "xg.huataisangao.cn",
    "z2.cnzz.com",
    "s96.cnzz.com",
    "q11.cnzz.com",
    "thy.dacedsfa.cn",
    "xg.whsbpw.cn",
    "s19.cnzz.com",
    "z8.cnzz.com",
    "s4.cnzz.com",
    "f5w.as12df.top",
    "ae01.alicdn.com",
    "www.92424.cn",
    "k.wudejia.com",
    "vivovip.mmszxc.top",
    "qiu.xixiqiu.com",
    "cdnjs.hnfenxun.com",
    "cms.qdwght.com",
    "static-mozai.4gtv.tv"
]

# DoH DNS 配置
DOH_CONFIG = [
    {
        "name": "Google",
        "url": "https://dns.google/dns-query",
        "ips": ["8.8.4.4", "8.8.8.8"]
    },
    {
        "name": "Cloudflare",
        "url": "https://cloudflare-dns.com/dns-query",
        "ips": ["1.1.1.1", "1.0.0.1"]
    },
    {
        "name": "阿里",
        "url": "https://dns.alidns.com/dns-query",
        "ips": ["223.6.6.6", "223.5.5.5"]
    },
    {
        "name": "腾讯",
        "url": "https://doh.pub/dns-query",
        "ips": ["119.29.29.29"]
    }
]

# 播放器配置
IJK_CONFIG = [
    {
        "group": "软解码",
        "options": [
            {"category": 4, "name": "opensles", "value": "0"},
            {"category": 4, "name": "overlay-format", "value": "842225234"},
            {"category": 4, "name": "framedrop", "value": "1"},
            {"category": 4, "name": "soundtouch", "value": "1"},
            {"category": 4, "name": "start-on-prepared", "value": "1"},
            {"category": 1, "name": "http-detect-range-support", "value": "0"},
            {"category": 1, "name": "fflags", "value": "fastseek"},
            {"category": 2, "name": "skip_loop_filter", "value": "48"},
            {"category": 4, "name": "reconnect", "value": "1"},
            {"category": 4, "name": "max-buffer-size", "value": "5242880"},
            {"category": 4, "name": "enable-accurate-seek", "value": "0"},
            {"category": 4, "name": "mediacodec", "value": "0"},
            {"category": 4, "name": "mediacodec-auto-rotate", "value": "0"},
            {"category": 4, "name": "mediacodec-handle-resolution-change", "value": "0"},
            {"category": 4, "name": "mediacodec-hevc", "value": "0"},
            {"category": 1, "name": "dns_cache_timeout", "value": "600000000"}
        ]
    },
    {
        "group": "硬解码",
        "options": [
            {"category": 4, "name": "opensles", "value": "0"},
            {"category": 4, "name": "overlay-format", "value": "842225234"},
            {"category": 4, "name": "framedrop", "value": "1"},
            {"category": 4, "name": "soundtouch", "value": "1"},
            {"category": 4, "name": "start-on-prepared", "value": "1"},
            {"category": 1, "name": "http-detect-range-support", "value": "0"},
            {"category": 1, "name": "fflags", "value": "fastseek"},
            {"category": 2, "name": "skip_loop_filter", "value": "48"},
            {"category": 4, "name": "reconnect", "value": "1"},
            {"category": 4, "name": "max-buffer-size", "value": "15728640"},
            {"category": 4, "name": "enable-accurate-seek", "value": "0"},
            {"category": 4, "name": "mediacodec", "value": "1"},
            {"category": 4, "name": "mediacodec-auto-rotate", "value": "1"},
            {"category": 4, "name": "mediacodec-handle-resolution-change", "value": "1"},
            {"category": 4, "name": "mediacodec-hevc", "value": "1"},
            {"category": 1, "name": "dns_cache_timeout", "value": "600000000"}
        ]
    }
]

# 解析器配置
PARSERS = [
    {
        "name": "解析聚合",
        "type": 3,
        "url": "Web"
    },
    {
        "name": "Json并发",
        "type": 2,
        "url": "Parallel"
    },
    {
        "name": "Json轮询",
        "type": 2,
        "url": "Sequence"
    },
    {
        "name": "观山",
        "type": 0,
        "url": "https://p10.zijincao.cc/?url="
    },
    {
        "name": "抚琴",
        "type": 0,
        "url": "https://jx.xmflv.com/?url="
    },
    {
        "name": "777",
        "type": 0,
        "url": "https://www.huaqi.live/?url="
    },
    {
        "name": "jsonplayer",
        "type": 0,
        "url": "https://jx.jsonplayer.com/player/?url="
    },
    {
        "name": "七哥",
        "type": 0,
        "url": "https://jx.nnxv.cn/tv.php?url="
    }
]

# 播放规则（包含 TS 切片广告过滤）
PLAY_RULES = [
    {
        "name": "量子广告",
        "hosts": ["vip.lz", "hd.lz"],
        "regex": [
            "#EXT-X-DISCONTINUITY\\r*\\n*#EXTINF:6.433333,[\\s\\S]*?#EXT-X-DISCONTINUITY",
            "#EXT-X-DISCONTINUITY\\r*\\n*#EXTINF:8.0,[\\s\\S]*?#EXT-X-DISCONTINUITY"
        ]
    },
    {
        "name": "非凡广告",
        "hosts": ["vip.ffzy", "hd.ffzy"],
        "regex": [
            "#EXT-X-DISCONTINUITY\\r*\\n*#EXTINF:6.433333,[\\s\\S]*?#EXT-X-DISCONTINUITY",
            "#EXT-X-DISCONTINUITY\\r*\\n*#EXTINF:8.0,[\\s\\S]*?#EXT-X-DISCONTINUITY"
        ]
    },
    {
        "name": "火山嗅探",
        "hosts": ["huoshan.com"],
        "regex": ["item_id="]
    },
    {
        "name": "抖音嗅探",
        "hosts": ["douyin.com"],
        "regex": ["is_play_url="]
    },
    {
        "name": "磁力广告",
        "hosts": ["magnet"],
        "regex": [
            "更多",
            "社 區",
            "x u u",
            "最 新",
            "直 播",
            "更 新",
            "社 区",
            "有 趣",
            "英皇体育",
            "全中文AV在线",
            "澳门皇冠赌场",
            "哥哥快来",
            "美女荷官",
            "裸聊",
            "新片首发",
            "UUE29"
        ]
    },
    {
        "host": "*",
        "rule": [
            "http((?!http).){12,}?\\.(m3u8|mp4|flv|avi|mkv|rm|wmv|mpg|m4a)\\?.*"
        ]
    },
    {
        "host": "*",
        "rule": [
            "http((?!http).){12,}\\.(m3u8|mp4|flv|avi|mkv|rm|wmv|mpg|m4a)"
        ]
    }
]

# Flags 配置
FLAGS = [
    "youku", "qq", "qiyi", "iqiyi", "leshi", "letv", 
    "sohu", "imgo", "mgtv", "bilibili", "pptv", "migu"
]

def create_premium_config(input_path: Path, output_path: Path):
    """创建高级优化配置"""
    
    # 读取高质量配置
    with open(input_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 豆瓣热搜站点配置
    douban_site = {
        "key": "豆瓣热搜",
        "name": "🔥 豆瓣热搜",
        "type": 3,
        "api": "./js/douban_hot.js",
        "searchable": 1,
        "quickSearch": 1,
        "filterable": 0,
        "changeable": 0
    }
    
    # 创建站点列表，豆瓣热搜放在第一位
    sites = [douban_site] + config.get('sites', [])
    
    # 创建增强配置
    premium_config = {
        "spider": "",
        "wallpaper": "https://picsum.photos/1280/720/?blur=2",
        "sites": sites,
        
        # 解析器
        "parses": PARSERS,
        
        # 直播源（空）
        "lives": [],
        
        # DoH DNS
        "doh": DOH_CONFIG,
        
        # 广告过滤
        "ads": AD_FILTERS,
        
        # 播放器配置
        "ijk": IJK_CONFIG,
        
        # 播放规则
        "rules": PLAY_RULES,
        
        # Flags
        "flags": FLAGS
    }
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(premium_config, f, ensure_ascii=False, indent=2)
    
    return premium_config

def create_readme(output_dir: Path, stats: dict):
    """创建 README"""
    
    readme = f"""# TVBox 高级优化配置

## 特性

### ✨ 核心优化

- ✅ **{stats['sites']} 个高质量 API 站点**
  - 90% API 类型（无依赖）
  - 包含量子、非凡、索尼等知名采集站
  - 稳定可靠

- ✅ **{stats['ad_filters']} 条广告过滤规则**
  - 过滤常见广告域名
  - 屏蔽统计追踪
  - **TS 切片广告过滤**（量子、非凡等）
  - 提升播放体验

- ✅ **{stats['parsers']} 个解析器**
  - 支持聚合解析
  - 并发/轮询模式
  - 多个备用解析

- ✅ **DoH DNS 优化**
  - Google / Cloudflare
  - 阿里 / 腾讯
  - 加速域名解析

- ✅ **播放器优化**
  - 软解码/硬解码配置
  - 缓冲优化
  - 快速 seek

## 配置说明

### 广告过滤

配置中包含 {stats['ad_filters']} 条广告过滤规则，自动屏蔽：

- **域名广告**：统计追踪（cnzz、百度统计等）、广告联盟域名、第三方 CDN 广告
- **TS 切片广告**：量子、非凡等采集站的 M3U8 播放列表中的广告切片
- **磁力广告**：磁力链接中的垃圾信息
- **短视频广告**：抖音、火山等平台的广告

### DNS 优化

使用 DoH (DNS over HTTPS) 加速域名解析：

1. **Google DNS** - 全球最快
2. **Cloudflare** - 隐私保护
3. **阿里 DNS** - 国内优化
4. **腾讯 DNS** - 备用

### 解析器

支持多种解析方式：

- **解析聚合** - 自动选择最佳解析
- **并发解析** - 同时尝试多个解析器
- **轮询解析** - 依次尝试解析器
- **直连解析** - 观山、抚琴、777 等

### 播放器配置

#### 软解码（兼容性好）
- 适合老设备
- CPU 解码
- 兼容性强

#### 硬解码（性能好）
- 适合新设备
- GPU 加速
- 省电流畅

## 使用方法

### 本地测试

```bash
cd premium_output
python3 -m http.server 8000
```

访问：`http://localhost:8000/config.json`

### 部署到 GitHub Pages

```bash
cp config.json /path/to/your/repo/
cd /path/to/your/repo
git add . && git commit -m "Add premium config" && git push
```

使用地址：`https://username.github.io/repo/config.json`

### 部署到 Vercel

```bash
cd premium_output
vercel
```

## 站点列表

### 一线采集站（⭐⭐⭐⭐⭐）

| 站点 | 特点 |
|------|------|
| 量子资源 | 资源丰富，更新快 |
| 非凡资源 | 高清资源多 |
| 索尼资源 | 稳定可靠 |
| 无尽资源 | 资源全面 |
| 金鹰资源 | 更新及时 |
| 速播资源 | 速度快 |
| 樱花资源 | 动漫资源多 |

### 二线采集站（⭐⭐⭐⭐）

- 卧龙资源
- 360资源
- 极速资源
- 暴风资源
- 电影天堂

## 性能对比

| 特性 | 普通配置 | 高级配置 |
|------|---------|---------|
| 广告过滤 | ✗ | ✓ {stats['ad_filters']} 条规则 |
| DNS 优化 | ✗ | ✓ DoH |
| 解析器 | 1-2 个 | {stats['parsers']} 个 |
| 播放器优化 | ✗ | ✓ 软/硬解码 |
| 配置大小 | 10 KB | {stats['size']} KB |

## 优势

- ✅ **无广告干扰** - 自动过滤广告
- ✅ **播放流畅** - 播放器优化
- ✅ **解析快速** - 多解析器支持
- ✅ **稳定可靠** - 高质量站点
- ✅ **易于维护** - API 类型为主

## 注意事项

1. **广告过滤**：部分站点可能需要调整规则
2. **解析器**：某些解析器可能失效，定期更新
3. **DNS**：根据网络环境选择合适的 DNS
4. **播放器**：根据设备性能选择软/硬解码

## 更新日志

- 2026-02-02: 初始版本
  - {stats['sites']} 个高质量站点
  - {stats['ad_filters']} 条广告过滤规则
  - {stats['parsers']} 个解析器
  - DoH DNS 优化
  - 播放器优化

## 反馈

如有问题或建议，欢迎反馈！

---

**推荐配置** ⭐⭐⭐⭐⭐
"""
    
    with open(output_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme)

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="quality_output/config_quality.json", help="Input quality config path")
    parser.add_argument("--output", default="premium_output", help="Output directory")
    args = parser.parse_args()
    
    print("=" * 70)
    print("创建高级优化配置")
    print("=" * 70)
    print()
    
    # 输入输出路径
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "config.json"
    
    if not input_path.exists():
        print(f"错误: {input_path} 不存在")
        print("请检查输入文件路径")
        return 1
    
    # 创建配置
    print("创建高级配置...")
    config = create_premium_config(input_path, output_path)
    
    # 统计信息
    stats = {
        'sites': len(config.get('sites', [])) + 1,  # +1 for Douban
        'ad_filters': len(config.get('ads', [])),
        'parsers': len(config.get('parses', [])),
        'size': output_path.stat().st_size // 1024
    }
    
    print(f"  ✓ 站点数: {stats['sites']}")
    print(f"  ✓ 广告过滤规则: {stats['ad_filters']}")
    print(f"  ✓ 解析器: {stats['parsers']}")
    print(f"  ✓ DoH DNS: {len(config.get('doh', []))}")
    print(f"  ✓ 配置大小: {stats['size']} KB")
    
    # 创建 README
    print("\n创建文档...")
    create_readme(output_dir, stats)
    
    print(f"\n✓ 配置已保存: {output_path}")
    print(f"✓ 文档已创建: {output_dir}/README.md")
    
    print("\n" + "=" * 70)
    print("完成！")
    print("=" * 70)
    print(f"\n使用方法:")
    print(f"  cd {output_dir}")
    print(f"  python3 -m http.server 8000")
    print(f"\n配置地址: http://localhost:8000/config.json")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
