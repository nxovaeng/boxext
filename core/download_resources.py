#!/usr/bin/env python3
"""
下载配置中引用的所有资源文件
"""
import json
import re
import asyncio
import aiohttp
from pathlib import Path
from urllib.parse import urljoin
from typing import Set, Dict, List
import sys

# 原始配置的基础 URL
SOURCE_BASE_URLS = {
    "qist-jsm": "https://qist.wyfc.qzz.io/",
    "qist-xiaosa": "https://raw.githubusercontent.com/qist/tvbox/refs/heads/master/xiaosa/",
    "cluntop-box": "https://clun.top/"
}

def extract_local_file_references(config: dict) -> Set[str]:
    """提取配置中引用的所有本地文件路径"""
    config_str = json.dumps(config, ensure_ascii=False)
    
    # 查找所有本地路径引用 "./xxx"
    local_paths = re.findall(r'"(\./[^"]+)"', config_str)
    
    # 清理路径
    clean_paths = set()
    for path in local_paths:
        clean_path = path.lstrip('./')
        clean_paths.add(clean_path)
    
    return clean_paths

async def download_file(session: aiohttp.ClientSession, url: str, output_path: Path, semaphore: asyncio.Semaphore) -> tuple:
    """
    下载单个文件
    
    Returns:
        (success, url, output_path, error_msg)
    """
    async with semaphore:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # 创建目录
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 保存文件
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    
                    return (True, url, output_path, None)
                else:
                    return (False, url, output_path, f"HTTP {response.status}")
        except asyncio.TimeoutError:
            return (False, url, output_path, "Timeout")
        except Exception as e:
            return (False, url, output_path, str(e))

async def download_resources_for_config(config_name: str, config_file: Path, output_dir: Path, max_concurrent: int = 10):
    """下载单个配置的所有资源"""
    
    # 读取配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 提取文件引用
    file_paths = extract_local_file_references(config)
    
    if not file_paths:
        print(f"  {config_name}: 没有需要下载的文件")
        return
    
    print(f"\n{config_name}: 找到 {len(file_paths)} 个文件")
    
    # 获取基础 URL
    base_url = SOURCE_BASE_URLS.get(config_name)
    if not base_url:
        print(f"  错误: 未知的配置源 {config_name}")
        return
    
    # 准备下载任务
    download_tasks = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async with aiohttp.ClientSession() as session:
        for file_path in file_paths:
            url = urljoin(base_url, file_path)
            output_path = output_dir / file_path
            
            # 跳过已存在的文件
            if output_path.exists():
                print(f"  ⊙ 跳过: {file_path} (已存在)")
                continue
            
            task = download_file(session, url, output_path, semaphore)
            download_tasks.append(task)
        
        if not download_tasks:
            print(f"  所有文件已存在")
            return
        
        # 执行下载
        print(f"  开始下载 {len(download_tasks)} 个文件...")
        results = await asyncio.gather(*download_tasks)
        
        # 统计结果
        success_count = 0
        failed_count = 0
        
        for success, url, output_path, error_msg in results:
            if success:
                success_count += 1
                file_size = output_path.stat().st_size
                print(f"  ✓ {output_path.relative_to(output_dir)} ({file_size} bytes)")
            else:
                failed_count += 1
                print(f"  ✗ {output_path.relative_to(output_dir)} - {error_msg}")
        
        print(f"\n  完成: {success_count} 成功, {failed_count} 失败")

async def download_all_resources(output_base: Path = Path("publish_output/local")):
    """下载所有配置的资源"""
    
    validated_dir = Path("validated_configs")
    config_files = list(validated_dir.glob("*_clean.json"))
    
    if not config_files:
        print("错误: 没有找到验证后的配置文件")
        return
    
    print("=" * 60)
    print("下载资源文件")
    print("=" * 60)
    
    for config_file in config_files:
        config_name = config_file.stem.replace("_clean", "")
        output_dir = output_base / config_name
        
        await download_resources_for_config(config_name, config_file, output_dir)
    
    # 下载合并配置的资源
    print("\n" + "=" * 60)
    print("下载合并配置的资源...")
    print("=" * 60)
    
    merged_output = output_base / "merged"
    
    for config_file in config_files:
        config_name = config_file.stem.replace("_clean", "")
        await download_resources_for_config(config_name, config_file, merged_output)

def create_download_summary(output_base: Path = Path("publish_output/local")):
    """创建下载摘要"""
    
    summary = []
    summary.append("# 资源下载摘要\n")
    
    for config_dir in sorted(output_base.iterdir()):
        if not config_dir.is_dir():
            continue
        
        config_name = config_dir.name
        summary.append(f"\n## {config_name}\n")
        
        # 统计各类文件
        file_types = {
            'js': list(config_dir.rglob("*.js")),
            'py': list(config_dir.rglob("*.py")),
            'jar': list(config_dir.rglob("*.jar")),
            'json': list(config_dir.rglob("*.json")),
        }
        
        total_size = 0
        for file_type, files in file_types.items():
            if files:
                type_size = sum(f.stat().st_size for f in files)
                total_size += type_size
                summary.append(f"- {file_type.upper()}: {len(files)} 个文件 ({type_size / 1024:.1f} KB)\n")
        
        summary.append(f"- **总计**: {total_size / 1024:.1f} KB\n")
        
        # 列出目录结构
        summary.append("\n目录结构:\n```\n")
        for item in sorted(config_dir.rglob("*")):
            if item.is_file() and item.name != "DOWNLOAD_SUMMARY.md":
                rel_path = item.relative_to(config_dir)
                summary.append(f"{rel_path}\n")
        summary.append("```\n")
    
    # 保存摘要
    summary_path = output_base / "DOWNLOAD_SUMMARY.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.writelines(summary)
    
    print(f"\n✓ 下载摘要已保存: {summary_path}")

async def download_specific_config(config_name: str):
    """下载特定配置的资源"""
    
    validated_dir = Path("validated_configs")
    config_file = validated_dir / f"{config_name}_clean.json"
    
    if not config_file.exists():
        print(f"错误: 配置文件不存在: {config_file}")
        return
    
    output_dir = Path("publish_output/local") / config_name
    
    print("=" * 60)
    print(f"下载 {config_name} 的资源")
    print("=" * 60)
    
    await download_resources_for_config(config_name, config_file, output_dir)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="下载 TVBox 配置资源文件")
    parser.add_argument(
        "config",
        nargs="?",
        help="配置名称 (qist-jsm, qist-xiaosa, cluntop-box, merged) 或留空下载全部"
    )
    parser.add_argument(
        "--output",
        default="publish_output/local",
        help="输出目录 (默认: publish_output/local)"
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=10,
        help="最大并发下载数 (默认: 10)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.config:
            # 下载特定配置
            asyncio.run(download_specific_config(args.config))
        else:
            # 下载所有配置
            asyncio.run(download_all_resources(Path(args.output)))
            create_download_summary(Path(args.output))
        
        print("\n" + "=" * 60)
        print("下载完成！")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n下载已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
