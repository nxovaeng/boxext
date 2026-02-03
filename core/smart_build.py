#!/usr/bin/env python3
"""
智能构建系统 - 完整流程
1. 从 config.json 读取在线源列表
2. 逐个验证和下载
3. 智能筛选高质量站点
4. 合并有效配置
5. 生成可部署的 publish 目录
"""
import json
from pathlib import Path
from .smart_validator import SmartValidator
from .filter_quality_sites import rate_site
import sys

def load_source_config(config_path: str = "config.json") -> dict:
    """加载源配置"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def smart_build(config_path: str = "config.json", output_dir: str = "smart_output",
                max_sites: int = 100, min_score: int = 30, skip_plugins: bool = False):
    """智能构建流程
    
    Args:
        config_path: 源配置文件路径 (default: config.json)
        output_dir: 输出目录 (default: smart_output)
    """
    
    print("=" * 70)
    print("TVBox 智能构建系统")
    print("=" * 70)
    print()
    
    # 1. 加载源配置
    print(f"步骤 1: 加载源配置 ({config_path})...")
    try:
        config = load_source_config(config_path)
        sources = config.get('sources', [])
        enabled_sources = [s for s in sources if s.get('enabled', True)]
        
        print(f"  找到 {len(sources)} 个源，{len(enabled_sources)} 个已启用")
    except Exception as e:
        print(f"  ✗ 加载配置失败: {e}")
        return 1
    
    if not enabled_sources:
        print("  ✗ 没有启用的源")
        return 1
    
    # 2. 创建输出目录
    output_base = Path(output_dir)
    output_base.mkdir(exist_ok=True)
    
    # 3. 验证每个源
    print(f"\n步骤 2: 验证和下载源...")
    
    validator = SmartValidator(timeout=15, max_workers=5)
    
    all_valid_sites = []
    all_parses = []
    all_lives = []
    
    seen_site_keys = set()
    seen_parse_names = set()
    
    source_reports = []
    
    for source in enabled_sources:
        name = source.get('name', 'unknown')
        url = source.get('url', '')
        
        if not url:
            print(f"\n跳过 {name}: 没有 URL")
            continue
        
        # 为每个源创建输出目录
        source_output = output_base / name
        
        # 验证源
        report = validator.validate_config(url, source_output)
        source_reports.append({
            'name': name,
            'url': url,
            'report': report
        })
        
        # 读取清理后的配置
        clean_config_path = source_output / 'config_clean.json'
        if clean_config_path.exists():
            with open(clean_config_path, 'r', encoding='utf-8') as f:
                clean_config = json.load(f)
            
            # 合并站点（去重）
            for site in clean_config.get('sites', []):
                key = site.get('key')
                if key and key not in seen_site_keys:
                    all_valid_sites.append(site)
                    seen_site_keys.add(key)
            
            # 合并解析器（去重）
            for parse in clean_config.get('parses', []):
                name_key = parse.get('name')
                if name_key and name_key not in seen_parse_names:
                    all_parses.append(parse)
                    seen_parse_names.add(name_key)
            
            # 合并直播源
            for live in clean_config.get('lives', []):
                if isinstance(live, dict):
                    all_lives.append(live)
    
    # 3.5 智能筛选高质量站点
    print(f"\n步骤 3: 智能筛选站点...")
    print(f"  原始站点数: {len(all_valid_sites)}")
    
    # 对所有站点评分
    rated_sites = []
    for site in all_valid_sites:
        rating = rate_site(site, allow_cloud=False)
        rated_sites.append({
            'site': site,
            'score': rating['score'],
            'reasons': rating['reasons'],
            'category': rating['category']
        })
    
    # 按分数排序
    rated_sites.sort(key=lambda x: x['score'], reverse=True)
    
    # 筛选高分站点
    filtered_sites = [
        rs['site'] for rs in rated_sites
        if rs['score'] >= min_score
    ][:max_sites]
    
    # 统计筛选结果
    category_stats = {}
    for rs in rated_sites[:max_sites]:
        cat = rs['category']
        category_stats[cat] = category_stats.get(cat, 0) + 1
    
    print(f"  筛选后站点数: {len(filtered_sites)} (最低分: {min_score}, 最多: {max_sites})")
    for cat, count in category_stats.items():
        print(f"    - {cat}: {count}")
    
    # 使用筛选后的站点
    all_valid_sites = filtered_sites
    
    # 4. 生成合并配置
    print(f"\n步骤 4: 生成合并配置...")
    
    # Helper function to normalize plugin paths
    def normalize_plugin_path(path):
        """Rewrite plugin paths to match our output directory structure"""
        if not path or not isinstance(path, str):
            return path
        
        # Handle relative paths like "./plugins/xxx.js" or "./lib/xxx.js"
        import re
        
        # Extract filename from various path formats
        if '.js' in path:
            # ./plugins/xxx.js -> ./js/xxx.js
            match = re.search(r'([^/]+\.js)$', path)
            if match:
                return f'./js/{match.group(1)}'
        elif '.py' in path:
            # ./plugins/xxx.py -> ./py/xxx.py
            match = re.search(r'([^/]+\.py)$', path)
            if match:
                return f'./py/{match.group(1)}'
        elif '.jar' in path:
            # ./plugins/jar/xxx.jar -> ./jar/xxx.jar
            match = re.search(r'([^/]+\.jar)$', path)
            if match:
                return f'./jar/{match.group(1)}'
        
        return path
    
    # Normalize paths in all sites
    normalized_sites = []
    for site in all_valid_sites:
        site_copy = site.copy()
        
        # Normalize api path
        if 'api' in site_copy:
            api = site_copy['api']
            if isinstance(api, str) and ('.js' in api or '.py' in api):
                site_copy['api'] = normalize_plugin_path(api)
        
        # Normalize ext path if it's a string containing plugin reference
        if 'ext' in site_copy:
            ext = site_copy['ext']
            if isinstance(ext, str) and ('.js' in ext or '.py' in ext):
                site_copy['ext'] = normalize_plugin_path(ext)
        
        # Normalize jar path
        if 'jar' in site_copy:
            jar = site_copy['jar']
            if isinstance(jar, str) and '.jar' in jar:
                site_copy['jar'] = normalize_plugin_path(jar)
        
        normalized_sites.append(site_copy)
    
    merged_config = {
        'spider': '',
        'wallpaper': './bgwall.jpg',
        'sites': normalized_sites,
        'parses': all_parses if all_parses else [
            {
                'name': '默认',
                'type': 0,
                'url': 'https://jx.xmflv.com/?url='
            }
        ],
        'lives': all_lives
    }
    
    # 保存合并配置
    merged_dir = output_base / 'merged'
    merged_dir.mkdir(exist_ok=True)
    
    merged_config_path = merged_dir / 'config.json'
    with open(merged_config_path, 'w', encoding='utf-8') as f:
        json.dump(merged_config, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ 合并配置已保存: {merged_config_path}")
    print(f"  - 站点: {len(all_valid_sites)}")
    print(f"  - 解析器: {len(all_parses)}")
    print(f"  - 直播源: {len(all_lives)}")
    
    # 5. 复制插件文件到合并目录
    total_files = 0
    
    if skip_plugins:
        print(f"\n步骤 5: 跳过插件整理 (--skip-plugins)")
    else:
        print(f"\n步骤 5: 整理插件文件...")
        
        (merged_dir / 'js').mkdir(exist_ok=True)
        (merged_dir / 'py').mkdir(exist_ok=True)
        (merged_dir / 'jar').mkdir(exist_ok=True)
        
        for source_report in source_reports:
            source_name = source_report['name']
            source_dir = output_base / source_name / 'plugins'
            
            if source_dir.exists():
                # 复制 JS 文件
                for js_file in source_dir.glob('*.js'):
                    dest = merged_dir / 'js' / js_file.name
                    if not dest.exists():
                        import shutil
                        shutil.copy2(js_file, dest)
                        total_files += 1
                
                # 复制 Python 文件
                for py_file in source_dir.glob('*.py'):
                    dest = merged_dir / 'py' / py_file.name
                    if not dest.exists():
                        import shutil
                        shutil.copy2(py_file, dest)
                        total_files += 1
                
                # 复制 JAR 文件
                jar_dir = source_dir / 'jar'
                if jar_dir.exists():
                    for jar_file in jar_dir.glob('*.jar'):
                        dest = merged_dir / 'jar' / jar_file.name
                        if not dest.exists():
                            import shutil
                            shutil.copy2(jar_file, dest)
                            total_files += 1
        
        print(f"  ✓ 已整理 {total_files} 个插件文件")
    
    # 6. 生成总报告
    print(f"\n步骤 5: 生成总报告...")
    
    summary_report = {
        'sources': source_reports,
        'merged': {
            'total_sites': len(all_valid_sites),
            'total_parses': len(all_parses),
            'total_lives': len(all_lives),
            'total_files': total_files,
            'config_path': str(merged_config_path)
        }
    }
    
    summary_path = output_base / 'build_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    
    # 生成 README
    readme_content = f"""# TVBox 智能构建结果

## 构建摘要

- **总站点数**: {len(all_valid_sites)}
- **解析器数**: {len(all_parses)}
- **直播源数**: {len(all_lives)}
- **插件文件**: {total_files}

## 源验证结果

"""
    
    for source_report in source_reports:
        name = source_report['name']
        report = source_report['report']
        valid = report.get('valid_sites', 0)
        total = report.get('total_sites', 0)
        
        readme_content += f"### {name}\n\n"
        readme_content += f"- URL: {source_report['url']}\n"
        readme_content += f"- 有效站点: {valid}/{total}\n"
        readme_content += f"- 详细报告: `{name}/validation_report.json`\n\n"
    
    readme_content += f"""
## 使用方法

### 本地测试

```bash
cd {merged_dir}
python3 -m http.server 8000
```

访问: `http://localhost:8000/config.json`

### 部署

将 `{merged_dir}` 目录部署到任意 HTTP 服务器。

### 在 TVBox 中使用

配置地址: `http://your-domain/config.json`

## 目录结构

```
{merged_dir}/
├── config.json      # 主配置文件
├── js/              # JavaScript 插件
├── py/              # Python 插件
└── jar/             # JAR 插件
```

## 注意事项

1. 所有站点都经过验证，只保留有效的
2. 插件文件已下载并分析
3. 定期重新构建以更新配置
"""
    
    readme_path = merged_dir / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  ✓ 总报告已保存: {summary_path}")
    print(f"  ✓ README 已生成: {readme_path}")
    
    # 7. 打印最终摘要
    print(f"\n{'='*70}")
    print("构建完成！")
    print(f"{'='*70}")
    print(f"\n输出目录: {output_base}/")
    print(f"\n推荐使用: {merged_dir}/")
    print(f"  - 配置文件: {merged_config_path}")
    print(f"  - 站点数: {len(all_valid_sites)}")
    print(f"  - 插件文件: {total_files}")
    
    print(f"\n下一步:")
    print(f"  1. 测试: cd {merged_dir} && python3 -m http.server 8000")
    print(f"  2. 部署到服务器")
    print(f"  3. 在 TVBox 中使用")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(smart_build())
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
