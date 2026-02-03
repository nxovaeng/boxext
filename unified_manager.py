#!/usr/bin/env python3
"""
TVBox Unified Manager (2026 Edition)
Integrates validation, building, and maintenance into a single CLI.

Usage:
    python3 unified_manager.py [COMMAND] [OPTIONS]

Commands:
    validate    Validate configuration sources.
    build       Build the final deployment package.
    clean       Clean up temporary files.
    scan        (New) Scan for potential security issues in plugins.
    premium     Generate premium configuration.
"""

import argparse
import sys
import shutil
import json
from pathlib import Path
from core.smart_validator import SmartValidator
# Import smart_build logic if possible, or reimplement it here cleanly
from core.smart_build import load_source_config

# Set up logging or print helpers
def print_header(title):
    print("=" * 60)
    print(f"TVBox Manager: {title}")
    print("=" * 60)

def cmd_validate(args):
    print_header("Source Validation")
    
    # Check if a specific URL is provided or if we should validate from config
    target_url = args.url
    if target_url:
        # If it's a local file, convert to file:// URI
        if Path(target_url).exists():
            target_url = Path(target_url).resolve().as_uri()
            
        print(f"Target: {target_url}")
        validator = SmartValidator(timeout=args.timeout, max_workers=args.workers)
        output_dir = Path(args.output)
        report = validator.validate_config(target_url, output_dir)
        if report.get('valid_sites', 0) > 0:
            print(f"\nSUCCESS: Found {report['valid_sites']} valid sites.")
        else:
            print("\nFAILURE: No valid sites found.")
            sys.exit(1)
    else:
        # Batch validation from config file (default: config.json)
        source_file = args.sources if hasattr(args, 'sources') and args.sources else "config.json"
        print(f"Mode: Batch Validation from {source_file}")
        
        try:
            if not Path(source_file).exists():
                print(f"Error: Source config '{source_file}' not found.")
                return

            with open(source_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            sources = [s for s in config.get('sources', []) if s.get('enabled', True)]
            if not sources:
                print(f"No enabled sources found in {source_file}")
                return
            
            print(f"Found {len(sources)} sources to validate.")
            
            validator = SmartValidator(timeout=args.timeout, max_workers=args.workers)
            output_base = Path(args.output)
            output_base.mkdir(exist_ok=True)
            
            for source in sources:
                name = source.get('name', 'unknown')
                url = source.get('url', '')
                if not url:
                    continue
                
                print(f"\nProcessing: {name}")
                # Local file handling for batch items
                if not url.startswith('http'):
                    if Path(url).exists():
                        url = Path(url).resolve().as_uri()
                    elif Path(source_file).parent.joinpath(url).exists():
                        url = Path(source_file).parent.joinpath(url).resolve().as_uri()
                
                validator.validate_config(url, output_base / name)
                
        except Exception as e:
            print(f"Error loading config: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def cmd_build(args):
    print_header("Build & Publish")
    from core.smart_build import smart_build
    
    config_path = args.config if hasattr(args, 'config') and args.config else "config.json"
    output_dir = args.output if hasattr(args, 'output') and args.output else "smart_output"
    include_cloud = args.include_cloud if hasattr(args, 'include_cloud') else False
    init_custom = args.init_custom if hasattr(args, 'init_custom') else False
    max_sites = args.max_sites if hasattr(args, 'max_sites') and args.max_sites else 100
    min_score = args.min_score if hasattr(args, 'min_score') and args.min_score else 30
    skip_plugins = args.skip_plugins if hasattr(args, 'skip_plugins') else False
    
    print(f"Config: {config_path}")
    print(f"Output: {output_dir}")
    print(f"Max Sites: {max_sites}")
    print(f"Min Score: {min_score}")
    print(f"Skip Plugins: {skip_plugins}")
    print(f"Include Cloud: {include_cloud}")
    if init_custom:
        print(f"Init Custom: ✓ (将初始化 custom/ 目录)")
    print()
    
    try:
        # Step 1: Build and validate with smart filtering
        ret_code = smart_build(
            config_path=config_path,
            output_dir=output_dir,
            max_sites=max_sites,
            min_score=min_score,
            skip_plugins=skip_plugins
        )
        if ret_code != 0:
            sys.exit(ret_code)
        
        # Step 2: Security scan
        print("\\n" + "=" * 60)
        print("Step: Security Scan...")
        print("=" * 60)
        
        from core.security import scan_plugins
        
        scan_dir = Path(output_dir)
        issues = scan_plugins(scan_dir)
        
        # JS regex scan
        js_patterns = [b'eval(', b'exec(', b'base64']
        for js_file in scan_dir.rglob('*.js'):
            try:
                content = js_file.read_bytes()
                for pat in js_patterns:
                    if pat in content:
                        issues.append({
                            "file": str(js_file),
                            "line": 0,
                            "type": "Medium",
                            "message": f"Suspicious JS pattern: {pat.decode()}"
                        })
            except:
                pass
        
        if not issues:
            print("  ✓ No security issues found")
        else:
            print(f"  ⚠ Found {len(issues)} potential issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"    [{issue['type']}] {Path(issue['file']).name}:{issue['line']} - {issue['message']}")
        
        # Step 2: Create filtered versions
        merged_dir = Path(output_dir) / 'merged'
        merged_config_path = merged_dir / 'config.json'
        
        if merged_config_path.exists():
            print("\n" + "=" * 60)
            print("Step: Creating filtered configs...")
            print("=" * 60)
            
            with open(merged_config_path, 'r', encoding='utf-8') as f:
                merged_config = json.load(f)
            
            all_sites = merged_config.get('sites', [])
            
            # Filter API-only sites (type=1 or csp_ without cloud patterns)
            api_sites = []
            full_sites = []
            
            cloud_patterns = ['Pan', 'Share', 'Wogg', 'Wobg', 'Moli', '阿里', '夸克', '网盘', 'alist']
            
            for site in all_sites:
                api = site.get('api', '')
                name = site.get('name', '')
                site_type = site.get('type', 0)
                
                # Check if it's a cloud/pan site
                is_cloud = False
                for pattern in cloud_patterns:
                    if pattern.lower() in api.lower() or pattern.lower() in name.lower():
                        is_cloud = True
                        break
                
                # API-only: type=1 (CMS API) or csp_ without cloud
                if site_type == 1 or (api.startswith('csp_') and not is_cloud):
                    api_sites.append(site)
                
                # Full sites: include everything (or filter cloud if not --include-cloud)
                if include_cloud or not is_cloud:
                    full_sites.append(site)
            
            # Create api-only config
            api_config = merged_config.copy()
            api_config['sites'] = api_sites
            
            api_dir = Path(output_dir) / 'api_only'
            api_dir.mkdir(exist_ok=True)
            with open(api_dir / 'config.json', 'w', encoding='utf-8') as f:
                json.dump(api_config, f, ensure_ascii=False, indent=2)
            
            print(f"  ✓ API-only config: {api_dir}/config.json ({len(api_sites)} sites)")
            
            # Update merged config with filtered sites
            if not include_cloud:
                merged_config['sites'] = full_sites
                with open(merged_config_path, 'w', encoding='utf-8') as f:
                    json.dump(merged_config, f, ensure_ascii=False, indent=2)
                print(f"  ✓ Merged config: {merged_config_path} ({len(full_sites)} sites)")
            else:
                print(f"  ✓ Merged config: {merged_config_path} ({len(all_sites)} sites)")
            
            # Step 3: If --init-custom, create custom/ with premium config
            if init_custom:
                print("\n" + "=" * 60)
                print("Step: Initializing custom/ with premium config...")
                print("=" * 60)
                
                # Import premium config constants
                try:
                    from core.create_premium_config import (
                        AD_FILTERS, DOH_CONFIG, IJK_CONFIG, PARSERS, PLAY_RULES, FLAGS
                    )
                except ImportError as e:
                    print(f"  ✗ 无法导入配置模块: {e}")
                    sys.exit(1)
                
                # 豆瓣热搜站点
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
                
                # 创建 premium 配置
                custom_config = {
                    "spider": "",
                    "wallpaper": "https://picsum.photos/1280/720/?blur=2",
                    "sites": [douban_site] + api_sites,
                    "parses": PARSERS,
                    "lives": [],
                    "doh": DOH_CONFIG,
                    "ads": AD_FILTERS,
                    "ijk": IJK_CONFIG,
                    "rules": PLAY_RULES,
                    "flags": FLAGS
                }
                
                # 保存到 custom/
                custom_dir = Path("custom")
                custom_dir.mkdir(exist_ok=True)
                custom_path = custom_dir / "config.json"
                
                with open(custom_path, 'w', encoding='utf-8') as f:
                    json.dump(custom_config, f, ensure_ascii=False, indent=2)
                
                print(f"  ✓ Custom config: {custom_path}")
                print(f"    - 站点数: {len(custom_config['sites'])} (1 豆瓣 + {len(api_sites)} API)")
                print(f"    - 广告过滤规则: {len(AD_FILTERS)}")
                print(f"    - DoH DNS: {len(DOH_CONFIG)}")
                print(f"    - 解析器: {len(PARSERS)}")
        
        print("\nBuild completed successfully!")
        if init_custom:
            print("可直接发布 custom/ 目录到 GitHub Pages")
        sys.exit(0)
        
    except Exception as e:
        print(f"Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_clean(args):
    print_header("Cleanup")
    targets = ['smart_output', 'publish_ready', 'merged_output', 'temp', 'logs']
    
    for t in targets:
        p = Path(t)
        if p.exists():
            print(f"Removing {t}...")
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        else:
            print(f"Skipping {t} (not found)")
    print("\nCleanup complete.")

def cmd_scan(args):
    print_header("Security Scan (Experimental)")
    print("Scanning for suspicious patterns in downloaded plugins...")
    
    base_dir = Path("smart_output")
    if not base_dir.exists():
        print("No build output found. Run 'build' or 'validate' first.")
        return

    from core.security import scan_plugins
    
    # Use the consolidated scanner (Python AST + JAR Heuristics)
    print("  Analysis: Deep Scan (Python AST + JAR Bytecode)...")
    issues = scan_plugins(base_dir)

    # Simple regex for JS files (AST assumes Python)
    print("  Analysis: JavaScript Regex Scan...")
    js_patterns = [b'eval(', b'exec(', b'base64']
    for js_file in base_dir.rglob('*.js'):
        try:
            content = js_file.read_bytes()
            for pat in js_patterns:
                if pat in content:
                    issues.append({
                        "file": str(js_file),
                        "line": 0,
                        "type": "Medium",
                        "message": f"Suspicious JS pattern: {pat.decode()}"
                    })
        except:
            pass

    if not issues:
        print("\nSUCCESS: No security issues found.")
    else:
        print(f"\nFound {len(issues)} potential security issues:")
        for issue in issues:
            try:
                # smart_output is relative, so issue['file'] might be relative to CWD already 
                # or relative to smart_output?
                # Let's resolve to absolute first
                abs_path = Path(issue['file']).resolve()
                display_path = abs_path.relative_to(Path.cwd())
            except ValueError:
                display_path = issue['file']
                
            print(f"  [{issue['type']}] {display_path}:{issue['line']} - {issue['message']}")

def cmd_premium(args):
    """生成高级配置: 独立功能，直接更新 custom/config.json"""
    print_header("Generating Premium Config")
    
    # 固定输出到 custom/ 目录
    custom_dir = Path("custom")
    custom_config = custom_dir / "config.json"
    
    # 导入 create_premium_config.py 中的配置常量
    try:
        from core.create_premium_config import (
            AD_FILTERS, DOH_CONFIG, IJK_CONFIG, PARSERS, PLAY_RULES, FLAGS
        )
    except ImportError as e:
        print(f"✗ 无法导入配置模块: {e}")
        sys.exit(1)
    
    # 如果 custom/config.json 存在，读取现有 sites
    if custom_config.exists():
        print(f"读取现有配置: {custom_config}")
        with open(custom_config, 'r', encoding='utf-8') as f:
            existing_config = json.load(f)
        sites = existing_config.get('sites', [])
        lives = existing_config.get('lives', [])
        print(f"  - 站点数: {len(sites)}")
    else:
        print("未找到现有配置，将创建新配置...")
        custom_dir.mkdir(parents=True, exist_ok=True)
        sites = []
        lives = []
    
    # 生成 premium 配置 (使用最新的广告过滤、DoH、播放器配置)
    premium_config = {
        "spider": "",
        "wallpaper": "https://picsum.photos/1280/720/?blur=2",
        "sites": sites,
        "parses": PARSERS,
        "lives": lives,
        "doh": DOH_CONFIG,
        "ads": AD_FILTERS,
        "ijk": IJK_CONFIG,
        "rules": PLAY_RULES,
        "flags": FLAGS
    }
    
    # 保存
    with open(custom_config, 'w', encoding='utf-8') as f:
        json.dump(premium_config, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 配置已更新: {custom_config}")
    print(f"  - 站点数: {len(sites)}")
    print(f"  - 广告过滤规则: {len(AD_FILTERS)}")
    print(f"  - DoH DNS: {len(DOH_CONFIG)}")
    print(f"  - 解析器: {len(PARSERS)}")
    print(f"  - 播放规则: {len(PLAY_RULES)}")
    
    print(f"\n可直接发布 custom/ 目录到 GitHub Pages")

def main():
    parser = argparse.ArgumentParser(description="TVBox Unified Manager")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Validate Command
    parser_val = subparsers.add_parser('validate', help='Validate sources')
    parser_val.add_argument('--url', help='Verify a specific URL (overrides config.json)')
    parser_val.add_argument('--sources', help='Path to source configuration file (default: config.json)')
    parser_val.add_argument('--output', default='smart_output', help='Output directory')
    parser_val.add_argument('--workers', type=int, default=5, help='Concurrency worker count')
    parser_val.add_argument('--timeout', type=int, default=15, help='Request timeout')

    # Build Command
    parser_build = subparsers.add_parser('build', help='Build deployment package from online sources')
    parser_build.add_argument('--config', help='Path to source config file (default: config.json)')
    parser_build.add_argument('--output', default='smart_output', help='Output directory (default: smart_output)')
    parser_build.add_argument('--max-sites', type=int, default=100, help='Maximum number of sites to include (default: 100)')
    parser_build.add_argument('--min-score', type=int, default=30, help='Minimum quality score for sites (default: 30)')
    parser_build.add_argument('--skip-plugins', action='store_true', help='Skip plugin download (faster build)')
    parser_build.add_argument('--include-cloud', action='store_true', help='Include Cloud/Pan sites in merged config')
    parser_build.add_argument('--init-custom', action='store_true', help='Initialize custom/ with API sites and premium config')
    
    # Clean Command
    parser_clean = subparsers.add_parser('clean', help='Remove temporary files')
    
    # Scan Command
    parser_scan = subparsers.add_parser('scan', help='Security scan of plugins')

    # Premium Command
    parser_premium = subparsers.add_parser('premium', help='Generate premium config (outputs to custom/)')

    args = parser.parse_args()
    
    if args.command == 'validate':
        cmd_validate(args)
    elif args.command == 'build':
        cmd_build(args)
    elif args.command == 'clean':
        cmd_clean(args)
    elif args.command == 'scan':
        cmd_scan(args)
    elif args.command == 'premium':
        cmd_premium(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
