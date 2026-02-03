#!/usr/bin/env python3
"""
将验证后的配置转换为可部署的 publish 格式
"""
import json
import os
import shutil
from pathlib import Path

def prepare_publish_structure(
    validated_config_path: str,
    output_dir: str = "publish_output",
    config_name: str = "config.json"
):
    """
    准备 publish 目录结构
    
    Args:
        validated_config_path: 验证后的配置文件路径
        output_dir: 输出目录
        config_name: 输出的配置文件名
    """
    # 创建输出目录结构
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    js_dir = output_path / "js"
    py_dir = output_path / "py"
    js_dir.mkdir(exist_ok=True)
    py_dir.mkdir(exist_ok=True)
    
    # 读取验证后的配置
    with open(validated_config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 简化配置，移除不必要的字段
    simplified_config = simplify_config(config)
    
    # 保存简化后的配置
    output_config_path = output_path / config_name
    with open(output_config_path, 'w', encoding='utf-8') as f:
        json.dump(simplified_config, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 配置已保存到: {output_config_path}")
    print(f"✓ 目录结构:")
    print(f"  {output_dir}/")
    print(f"  ├── config.json")
    print(f"  ├── js/")
    print(f"  └── py/")
    
    return output_path

def simplify_config(config: dict) -> dict:
    """
    简化配置，只保留必要字段
    """
    # 基础配置
    simplified = {
        "spider": config.get("spider", ""),
        "wallpaper": config.get("wallpaper", "./bgwall.jpg")
    }
    
    # 站点配置
    if "sites" in config:
        simplified["sites"] = config["sites"]
    
    # 解析配置
    if "parses" in config:
        simplified["parses"] = config["parses"]
    else:
        # 添加默认解析
        simplified["parses"] = [
            {
                "name": "默认",
                "type": 0,
                "url": "https://jx.xmflv.com/?url="
            }
        ]
    
    # 直播配置（可选）
    if "lives" in config and config["lives"]:
        # 过滤掉本地路径的直播源
        lives = []
        for live in config["lives"]:
            if isinstance(live, dict):
                url = live.get("url", "")
                # 跳过本地文件路径
                if not url.startswith("./"):
                    lives.append(live)
        if lives:
            simplified["lives"] = lives
    else:
        simplified["lives"] = []
    
    return simplified

def merge_configs(config_paths: list, output_dir: str = "publish_output"):
    """
    合并多个配置文件
    
    Args:
        config_paths: 配置文件路径列表
        output_dir: 输出目录
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    js_dir = output_path / "js"
    py_dir = output_path / "py"
    js_dir.mkdir(exist_ok=True)
    py_dir.mkdir(exist_ok=True)
    
    merged_sites = []
    merged_parses = []
    merged_lives = []
    
    seen_site_keys = set()
    seen_parse_names = set()
    
    for config_path in config_paths:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 合并站点（去重）
        if "sites" in config:
            for site in config["sites"]:
                key = site.get("key")
                if key and key not in seen_site_keys:
                    merged_sites.append(site)
                    seen_site_keys.add(key)
        
        # 合并解析（去重）
        if "parses" in config:
            for parse in config["parses"]:
                name = parse.get("name")
                if name and name not in seen_parse_names:
                    merged_parses.append(parse)
                    seen_parse_names.add(name)
        
        # 合并直播源
        if "lives" in config:
            for live in config["lives"]:
                if isinstance(live, dict):
                    url = live.get("url", "")
                    if not url.startswith("./"):
                        merged_lives.append(live)
    
    # 创建合并后的配置
    merged_config = {
        "spider": "",
        "wallpaper": "./bgwall.jpg",
        "sites": merged_sites,
        "parses": merged_parses if merged_parses else [
            {
                "name": "默认",
                "type": 0,
                "url": "https://jx.xmflv.com/?url="
            }
        ],
        "lives": merged_lives
    }
    
    # 保存合并后的配置
    output_config_path = output_path / "config.json"
    with open(output_config_path, 'w', encoding='utf-8') as f:
        json.dump(merged_config, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 合并配置已保存到: {output_config_path}")
    print(f"✓ 统计:")
    print(f"  - 站点数: {len(merged_sites)}")
    print(f"  - 解析数: {len(merged_parses)}")
    print(f"  - 直播源: {len(merged_lives)}")
    
    return output_path

def create_readme(output_dir: str):
    """创建 README 文件"""
    readme_content = """# TVBox 配置部署

## 部署说明

将此目录部署到任意 HTTP 服务器即可使用。

## 目录结构

```
.
├── config.json      # 主配置文件
├── bgwall.jpg       # 背景图片（可选）
├── js/              # JavaScript 插件目录
└── py/              # Python 插件目录
```

## 使用方法

1. 将整个目录上传到 HTTP 服务器
2. 在 TVBox 应用中配置地址：`http://your-domain/config.json`

## 部署示例

### GitHub Pages
1. 将文件推送到 GitHub 仓库
2. 启用 GitHub Pages
3. 使用地址：`https://username.github.io/repo/config.json`

### Vercel
1. 导入 GitHub 仓库到 Vercel
2. 部署后使用：`https://your-project.vercel.app/config.json`

### 自建服务器
```bash
# 使用 Python 简单 HTTP 服务器
python3 -m http.server 8000

# 使用 Nginx
# 将文件放到 /var/www/html/ 目录
```

## 注意事项

- 确保服务器支持 CORS（跨域资源共享）
- 建议使用 HTTPS 协议
- 定期更新配置文件
"""
    
    readme_path = Path(output_dir) / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ README 已创建: {readme_path}")

if __name__ == "__main__":
    import sys
    
    print("TVBox 配置发布准备工具")
    print("=" * 50)
    
    # 获取所有验证后的配置
    validated_dir = Path("validated_configs")
    if not validated_dir.exists():
        print("错误: validated_configs 目录不存在")
        sys.exit(1)
    
    config_files = list(validated_dir.glob("*_clean.json"))
    
    if not config_files:
        print("错误: 没有找到验证后的配置文件")
        sys.exit(1)
    
    print(f"\n找到 {len(config_files)} 个配置文件:")
    for i, config_file in enumerate(config_files, 1):
        print(f"  {i}. {config_file.name}")
    
    print("\n选择操作:")
    print("  1. 单独转换每个配置")
    print("  2. 合并所有配置")
    print("  3. 两者都做")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    output_base = "publish_output"
    
    if choice in ["1", "3"]:
        print("\n" + "=" * 50)
        print("单独转换配置...")
        print("=" * 50)
        for config_file in config_files:
            name = config_file.stem.replace("_clean", "")
            output_dir = f"{output_base}/{name}"
            print(f"\n处理: {config_file.name}")
            prepare_publish_structure(str(config_file), output_dir)
            create_readme(output_dir)
    
    if choice in ["2", "3"]:
        print("\n" + "=" * 50)
        print("合并所有配置...")
        print("=" * 50)
        merge_output = f"{output_base}/merged"
        merge_configs([str(f) for f in config_files], merge_output)
        create_readme(merge_output)
    
    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)
    print(f"\n输出目录: {output_base}/")
    print("\n下一步:")
    print("  1. 复制输出目录到你的 HTTP 服务器")
    print("  2. 或推送到 GitHub Pages")
    print("  3. 在 TVBox 中使用配置地址")
