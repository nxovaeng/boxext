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
                exclude_cloud: bool = True):
    """智能配置验证与分源保存流程
    
    Args:
        config_path: 源配置文件路径 (default: config.json)
        output_dir: 输出目录 (default: smart_output)
        exclude_cloud: 是否排除网盘及依赖网盘的站点
    """
    
    print("=" * 70)
    print("TVBox 智能配置分源提取系统")
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
    print(f"\n步骤 2: 验证并下载每个源...")
    
    validator = SmartValidator(timeout=15, max_workers=5)
    
    source_reports = []
    
    for source in enabled_sources:
        name = source.get('name', 'unknown')
        url = source.get('url', '')
        
        if not url:
            print(f"\n跳过 {name}: 没有 URL")
            continue
        
        # 为每个源创建独立的输出目录
        source_output = output_base / name
        
        # 验证源并剥离失效或网盘资源
        report = validator.validate_config(url, source_output, exclude_cloud=exclude_cloud)
        source_reports.append({
            'name': name,
            'url': url,
            'report': report
        })
    
    # 4. 生成总报告
    print(f"\n步骤 3: 生成总报告...")
    
    summary_report = {
        'sources': source_reports
    }
    
    summary_path = output_base / 'build_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    
    # 生成 README
    readme_content = f"# TVBox 配置分源验证结果\n\n"
    readme_content += f"## 验证报告\n\n"
    
    for source_report in source_reports:
        name = source_report['name']
        report = source_report['report']
        valid = report.get('valid_sites', 0)
        total = report.get('total_sites', 0)
        
        readme_content += f"### {name}\n\n"
        readme_content += f"- URL: {source_report['url']}\n"
        readme_content += f"- 有效站点: {valid}/{total}\n"
        readme_content += f"- 本地配置: `{name}/config.json`\n"
        readme_content += f"- 验证报告: `{name}/validation_report.json`\n\n"
    
    readme_content += f"""
## 使用方法

每个源都已经独立存放并包含了运行所需的插件（JS/JAR/PY）。已排除所有失效源和网盘配置。

### 本地测试

```bash
cd {output_dir}
python3 -m http.server 8000
```

访问各个分源配置，例如：`http://localhost:8000/源名称/config.json`

### 部署

将整个 `{output_dir}` 目录部署到任意 HTTP 服务器或 GitHub Pages。
"""
    
    readme_path = output_base / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  ✓ 总报告已保存: {summary_path}")
    print(f"  ✓ README 已生成: {readme_path}")
    
    # 5. 打印最终摘要
    print(f"\n{'='*70}")
    print("验证与提取完成！")
    print(f"{'='*70}")
    print(f"\n输出目录: {output_base}/")
    
    print(f"\n下一步:")
    print(f"  1. 测试: cd {output_base} && python3 -m http.server 8000")
    print(f"  2. 将输出目录部署到服务器。各个分源可独立使用！")
    
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
