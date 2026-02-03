#!/usr/bin/env python3
"""
筛选高质量站点
优先选择：
1. API 类型（type: 1）- 稳定、无依赖
2. 知名采集站 - 量子、非凡、索尼等
3. 可搜索、快速搜索的站点
"""
import json
from pathlib import Path
from typing import List, Dict
import re


# 知名高质量采集站关键词
QUALITY_KEYWORDS = [
    '量子', '非凡', '索尼', '无尽', '金鹰', '速播', '樱花',
    '豆瓣', 'lziapi', 'ffzyapi', 'suoniapi', 'wujinapi',
    'jyzyapi', 'subocaiji', 'apiyhzy', 'dbzy'
]

# 网盘类源的关键词（需要排除）
NETDISK_KEYWORDS = [
    '网盘', '分享', 'share', 'pan', 'disk', 'drive',
    '阿里', 'ali', 'aliyun', 'alishare',
    '夸克', 'quark',
    '115', '123',
    '迅雷', 'thunder',
    'uc', 'ucshare',
    'pikpak',
    'samba',
    '玩偶', 'wogg', 'wobg',
    '蜡笔', 'labi',
    '木偶', 'mogg',
    '土豆', 'tudou',
    '小米', 'xiaomi',
    '表哥', 'biaoge',
    '老哥', 'laoge',
    'tg', 'telegram',
    'alist',
    'webdav',
    '云盘', 'yunpan',
    '资源分享', 'pushshare',
    '书籍', 'ebook'
]

# 需要排除的 API 类型
EXCLUDE_API_PATTERNS = [
    r'csp_.*Share',  # 所有 Share 类
    r'csp_.*Pan',    # 所有 Pan 类
    r'csp_Wogg',
    r'csp_Wobg',
    r'csp_Moli',
    r'csp_TGYunPan',
    r'csp_AliShare',
    r'csp_QuarkShare',
    r'csp_ThunderShare',
    r'csp_P115Share',
    r'csp_UCShare',
    r'csp_SambaShare',
    r'csp_PikPakShare',
    r'csp_PushShare',
]



def rate_site(site: dict, allow_cloud: bool = False) -> dict:
    """
    评分站点质量
    返回: {score, reasons, category}
    """
    score = 0
    reasons = []
    
    site_type = site.get('type', 0)
    api = site.get('api', '')
    name = site.get('name', '')
    searchable = site.get('searchable', 0)
    quick_search = site.get('quickSearch', 0)
    
    # 0. 网盘过滤 (需要账号，大幅扣分) - UNLESS allowed
    if not allow_cloud:
        # Check Keywords
        for kw in NETDISK_KEYWORDS:
            if kw.lower() in name.lower() or kw.lower() in api.lower():
                score -= 100
                reasons.append(f'网盘资源({kw})')
                break
        
        # Check Patterns (if not already penalized)
        if score >= 0:
            for pattern in EXCLUDE_API_PATTERNS:
                if re.search(pattern, api, re.IGNORECASE):
                    score -= 100
                    reasons.append(f'网盘插件({pattern})')
                    break
            
    # 1. API 类型加分（最稳定）
    if site_type == 1:
        score += 50
        reasons.append('API类型（稳定）')
        category = 'api'
    elif api.startswith('csp_'):
        score += 20
        reasons.append('CSP插件')
        category = 'csp'
    elif '.js' in api:
        score += 10
        reasons.append('JS插件')
        category = 'js'
    elif '.py' in api:
        score += 10
        reasons.append('Python插件')
        category = 'python'
    else:
        category = 'unknown'
    
    # 2. 知名采集站加分
    for keyword in QUALITY_KEYWORDS:
        if keyword in name or keyword in api:
            score += 30
            reasons.append(f'知名站点({keyword})')
            break
    
    # 3. 功能加分
    if searchable:
        score += 10
        reasons.append('可搜索')
    
    if quick_search:
        score += 10
        reasons.append('快速搜索')
    
    # 4. API 地址加分
    if api.startswith('http'):
        score += 20
        reasons.append('在线API')
    
    return {
        'score': score,
        'reasons': reasons,
        'category': category
    }

def filter_quality_sites(config_path: Path, min_score: int = 50, allow_cloud: bool = False) -> dict:
    """筛选高质量站点"""
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    sites = config.get('sites', [])
    
    # 评分所有站点
    rated_sites = []
    for site in sites:
        rating = rate_site(site, allow_cloud=allow_cloud)
        rated_sites.append({
            'site': site,
            'rating': rating
        })
    
    # 按分数排序
    rated_sites.sort(key=lambda x: x['rating']['score'], reverse=True)
    
    # 筛选高分站点
    quality_sites = [
        rs for rs in rated_sites 
        if rs['rating']['score'] >= min_score
    ]
    
    # 按类型分组
    by_category = {
        'api': [],
        'csp': [],
        'js': [],
        'python': [],
        'unknown': []
    }
    
    for rs in quality_sites:
        category = rs['rating']['category']
        by_category[category].append(rs)
    
    return {
        'total_sites': len(sites),
        'quality_sites': len(quality_sites),
        'rated_sites': rated_sites,
        'quality_list': quality_sites,
        'by_category': by_category
    }

def analyze_all_configs(input_dir: Path, output_dir: Path, allow_cloud: bool = False):
    """分析所有配置"""
    
    if not input_dir.exists():
        print(f"错误: {input_dir} 目录不存在 (请先运行 validate 或 build)")
        return
    
    # Support both structure: flat JSONs or subfolders with config_clean.json
    config_files = list(input_dir.rglob("*_clean.json"))
    if not config_files:
        # Try looking for just .json files if no _clean.json found (maybe raw validation)
        config_files = list(input_dir.glob("*.json"))
    
    if not config_files:
        print(f"在 {input_dir} 中未找到配置文件")
        return

    print("=" * 70)
    print(f"高质量站点筛选 (Input: {input_dir})")
    print("=" * 70)
    print()
    
    all_quality_sites = []
    
    for config_file in config_files:
        # Skip output files we generated (circular check)
        if "quality" in config_file.name or "premium" in config_file.name:
            continue
            
        config_name = config_file.stem.replace("_clean", "")
        print(f"分析: {config_name}")
        
        try:
            result = filter_quality_sites(config_file, min_score=50, allow_cloud=allow_cloud)
            print(f"  总站点: {result['total_sites']}")
            print(f"  高质量: {result['quality_sites']}")
            all_quality_sites.extend(result['quality_list'])
        except Exception as e:
            print(f"  出错: {e}")
        
        print()
        
    # 创建合并的高质量配置
    print("=" * 70)
    print("创建合并的高质量配置")
    print("=" * 70)
    print()
    
    # 去重
    seen_keys = set()
    unique_quality_sites = []
    
    for rs in all_quality_sites:
        site = rs['site']
        key = site.get('key')
        if key and key not in seen_keys:
            unique_quality_sites.append(rs)
            seen_keys.add(key)
    
    # 按分数排序
    unique_quality_sites.sort(key=lambda x: x['rating']['score'], reverse=True)
    
    # 按类型分组 for stats
    by_category = {
        'api': [],
        'csp': [],
        'js': [],
        'python': []
    }
    
    for rs in unique_quality_sites:
        category = rs['rating']['category']
        if category in by_category:
            by_category[category].append(rs)
            
    print(f"总高质量站点: {len(unique_quality_sites)}")
    
    # 创建配置文件
    quality_config = {
        'spider': '',
        'wallpaper': './bgwall.jpg',
        'sites': [rs['site'] for rs in unique_quality_sites],
        'parses': [
            {
                'name': '默认',
                'type': 0,
                'url': 'https://jx.xmflv.com/?url='
            }
        ],
        'lives': []
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "config_quality.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(quality_config, f, ensure_ascii=False, indent=2)
    
    print(f"高质量配置已保存: {output_path}")
    
    return unique_quality_sites

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="validated_configs", help="Input directory containing validated configs")
    parser.add_argument("--output", default="quality_output", help="Output directory")
    parser.add_argument("--include-cloud", action='store_true', help="Include Cloud/Pan sites")
    args = parser.parse_args()
    
    analyze_all_configs(Path(args.input), Path(args.output), allow_cloud=args.include_cloud)
