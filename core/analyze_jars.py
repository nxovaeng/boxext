#!/usr/bin/env python3
"""
分析配置中的 JAR 文件使用情况
"""
import json
from pathlib import Path
from collections import defaultdict

def analyze_jar_usage(config_path: Path):
    """分析单个配置的 JAR 使用情况"""
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 全局 spider JAR
    global_spider = config.get('spider', '')
    if ';md5;' in global_spider:
        global_spider = global_spider.split(';md5;')[0]
    
    # 统计站点
    total_sites = len(config.get('sites', []))
    csp_sites = []
    jar_usage = defaultdict(list)
    
    for site in config.get('sites', []):
        api = site.get('api', '')
        key = site.get('key', 'unknown')
        name = site.get('name', 'unknown')
        
        if api.startswith('csp_'):
            csp_sites.append({
                'key': key,
                'name': name,
                'api': api,
                'jar': site.get('jar', '')
            })
            
            # 记录 JAR 使用
            jar = site.get('jar', '')
            if ';md5;' in jar:
                jar = jar.split(';md5;')[0]
            
            if jar:
                jar_usage[jar].append(name)
            else:
                jar_usage['<global>'].append(name)
    
    return {
        'config': config_path.name,
        'total_sites': total_sites,
        'csp_sites': len(csp_sites),
        'global_spider': global_spider,
        'jar_usage': dict(jar_usage),
        'csp_details': csp_sites
    }

def analyze_all_configs():
    """分析所有配置"""
    
    validated_dir = Path("validated_configs")
    if not validated_dir.exists():
        print("错误: validated_configs 目录不存在")
        return
    
    config_files = list(validated_dir.glob("*_clean.json"))
    
    print("=" * 70)
    print("JAR 文件使用分析")
    print("=" * 70)
    print()
    
    all_jars = set()
    all_results = []
    
    for config_file in config_files:
        result = analyze_jar_usage(config_file)
        all_results.append(result)
        
        print(f"配置: {result['config']}")
        print(f"  总站点: {result['total_sites']}")
        print(f"  CSP 站点: {result['csp_sites']}")
        print(f"  全局 JAR: {result['global_spider'] or '(无)'}")
        
        if result['global_spider']:
            all_jars.add(result['global_spider'])
        
        if result['jar_usage']:
            print(f"  JAR 使用情况:")
            for jar, sites in result['jar_usage'].items():
                if jar != '<global>':
                    all_jars.add(jar)
                print(f"    {jar}: {len(sites)} 个站点")
                if len(sites) <= 5:
                    for site in sites:
                        print(f"      - {site}")
                else:
                    for site in sites[:3]:
                        print(f"      - {site}")
                    print(f"      ... 还有 {len(sites) - 3} 个")
        print()
    
    # 总结
    print("=" * 70)
    print("总结")
    print("=" * 70)
    print(f"\n唯一的 JAR 文件数: {len(all_jars)}")
    print("\nJAR 文件列表:")
    for i, jar in enumerate(sorted(all_jars), 1):
        print(f"  {i}. {jar}")
    
    # 统计哪些站点使用了哪些 JAR
    print("\n" + "=" * 70)
    print("JAR 文件详细使用情况")
    print("=" * 70)
    
    jar_to_sites = defaultdict(set)
    
    for result in all_results:
        for jar, sites in result['jar_usage'].items():
            if jar == '<global>':
                jar = result['global_spider'] or '<none>'
            for site in sites:
                jar_to_sites[jar].add(f"{result['config']}: {site}")
    
    for jar in sorted(jar_to_sites.keys()):
        sites = jar_to_sites[jar]
        print(f"\n{jar}:")
        print(f"  使用站点数: {len(sites)}")
        if len(sites) <= 10:
            for site in sorted(sites):
                print(f"    - {site}")
        else:
            for site in sorted(list(sites)[:5]):
                print(f"    - {site}")
            print(f"    ... 还有 {len(sites) - 5} 个")
    
    # 保存分析结果
    output = {
        'unique_jars': sorted(list(all_jars)),
        'jar_count': len(all_jars),
        'configs': all_results,
        'jar_to_sites': {jar: sorted(list(sites)) for jar, sites in jar_to_sites.items()}
    }
    
    output_path = Path("jar_analysis.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析结果已保存到: {output_path}")

if __name__ == "__main__":
    analyze_all_configs()
