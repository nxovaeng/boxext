#!/usr/bin/env python3
"""
智能验证器 - 完整的配置验证和构建流程
1. 访问在线源
2. 解析配置
3. 判断类型（网站API/JS/Python）
4. 验证有效性
5. 分析插件内部地址
6. 只保留有效配置
"""
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional
import hashlib

class SmartValidator:
    def __init__(self, timeout=15, max_workers=5):
        self.timeout = timeout
        self.max_workers = max_workers
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def download_config(self, url: str) -> Optional[dict]:
        """下载在线配置"""
        try:
            print(f"  下载配置: {url}")
            req = urllib.request.Request(url, headers=self.session_headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content = response.read().decode('utf-8')
                return json.loads(content)
        except Exception as e:
            print(f"  ✗ 下载失败: {e}")
            return None
    
    def classify_site(self, site: dict) -> str:
        """
        判断站点类型
        返回: 'api', 'js', 'python', 'jar', 'unknown'
        """
        api = site.get('api', '')
        site_type = site.get('type', 0)
        
        # Type 1 通常是直接API
        if site_type == 1:
            return 'api'
        
        # 判断文件扩展名
        if '.js' in api or api.endswith('.js'):
            return 'js'
        elif '.py' in api or api.endswith('.py'):
            return 'python'
        elif '.jar' in api or site.get('jar'):
            return 'jar'
        elif api.startswith('csp_'):
            return 'jar'  # CSP 插件需要 jar
        elif api.startswith('http'):
            return 'api'
        
        return 'unknown'
    
    def test_api_site(self, site: dict, base_url: str = '') -> Tuple[bool, str]:
        """
        测试 API 类型的站点
        返回: (是否有效, 错误信息)
        """
        api = site.get('api', '')
        
        # 构建完整 URL
        if not api.startswith('http'):
            if base_url:
                api = urljoin(base_url, api)
            else:
                return False, "相对路径但无基础URL"
        
        try:
            # 尝试访问 API
            req = urllib.request.Request(api, headers=self.session_headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    # 尝试解析返回内容
                    content = response.read()
                    # 检查是否是有效的 XML/JSON
                    if b'<rss' in content or b'<?xml' in content or b'{' in content:
                        return True, "API 可访问"
                    else:
                        return False, "返回内容格式异常"
                else:
                    return False, f"HTTP {response.status}"
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            return False, f"URL Error: {e.reason}"
        except Exception as e:
            return False, str(e)
    
    def download_plugin(self, url: str, output_path: Path, depth: int = 0, max_depth: int = 3) -> Tuple[bool, Optional[bytes]]:
        """
        下载插件文件 (支持递归下载依赖)
        返回: (是否成功, 文件内容)
        """
        if depth > max_depth:
            return False, None
            
        try:
            # URL 编码
            if '://' in url:
                protocol, rest = url.split('://', 1)
                if '/' in rest:
                    domain, path = rest.split('/', 1)
                    encoded_path = quote(path, safe='/:?=&%')
                    url = f"{protocol}://{domain}/{encoded_path}"
            
            req = urllib.request.Request(url, headers=self.session_headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    content = response.read()
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(content)
                        
                    # 递归分析依赖 (仅限 JS)
                    if output_path.suffix == '.js' and depth < max_depth:
                        self._process_js_dependencies(url, content, output_path, depth, max_depth)
                        
                    return True, content
                else:
                    return False, None
        except Exception as e:
            print(f"    下载失败: {e}")
            return False, None
    
    def _process_js_dependencies(self, base_url: str, content: bytes, current_path: Path, depth: int, max_depth: int):
        """处理 JS 依赖下载"""
        try:
            text = content.decode('utf-8', errors='ignore')
            deps = self.find_js_dependencies(text)
            
            for dep in deps:
                # 忽略远程绝对 URL (通常 CDN 不需要下载，或者根据需求修改)
                if dep.startswith('http'):
                    continue
                    
                # 解析依赖 URL
                # 假设 dep 是 "./drpy-core.js" 或 "drpy-core.js"
                # base_url 是 "http://.../some_plugin.js"
                # 则 dep_url 是 "http://.../drpy-core.js"
                
                # Handling path traversal relative to URL
                if '/' in base_url:
                    base_dir_url = base_url.rsplit('/', 1)[0] + '/'
                else:
                    base_dir_url = base_url + '/'
                    
                dep_url = urljoin(base_dir_url, dep)
                
                # 解析本地输出路径
                # 保持相同的相对结构
                # current_path 是 ".../plugins/some_plugin.js"
                # dep_path 应该是 ".../plugins/drpy-core.js"
                
                # 简单的相对路径计算
                # 注意：这里假设 dep 是相对路径
                dep_path = current_path.parent / dep
                dep_path = dep_path.resolve()
                
                # 防止写出到 smart_output 之外 (简单安全检查)
                # print(f"    [Dep] Found dependency: {dep} -> Downloading to {dep_path.name}")
                
                if not dep_path.exists():
                     self.download_plugin(dep_url, dep_path, depth + 1, max_depth)
                     
        except Exception as e:
            # print(f"    依赖分析失败: {e}")
            pass

    def find_js_dependencies(self, text: str) -> List[str]:
        """查找 JS 代码中的依赖引用"""
        deps = set()
        
        # 1. import ... from "..."
        # 2. import "..."
        # 3. from "..." (part of import)
        import_pattern = r'(?:import|from)\s+[\'"]([^\'"]+)[\'"]'
        
        # 4. require("...")
        require_pattern = r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        
        for p in [import_pattern, require_pattern]:
            matches = re.findall(p, text)
            for m in matches:
                if not m.startswith('data:') and not m.startswith('js:'):
                    deps.add(m)
                    
        return list(deps)

    def analyze_js_plugin(self, content: bytes) -> Dict[str, List[str]]:
        """
        分析 JS 插件内部使用的地址
        返回: {'urls': [...], 'domains': [...]}
        """
        try:
            text = content.decode('utf-8', errors='ignore')
        except:
            return {'urls': [], 'domains': []}
        
        urls = set()
        domains = set()
        
        # 匹配 URL 模式
        url_patterns = [
            r'https?://[^\s\'"<>]+',  # 标准 URL
            r'//[a-zA-Z0-9][a-zA-Z0-9-]+\.[^\s\'"<>]+',  # 协议相对 URL
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # 清理 URL
                url = match.rstrip('",;)}]')
                if url:
                    urls.add(url)
                    # 提取域名
                    try:
                        parsed = urlparse(url if url.startswith('http') else 'http:' + url)
                        if parsed.netloc:
                            # 忽略本地地址
                            if '127.0.0.1' in parsed.netloc or 'localhost' in parsed.netloc:
                                continue
                            domains.add(parsed.netloc)
                    except:
                        pass
        

        
        return {
            'urls': sorted(list(urls)),
            'domains': sorted(list(domains))
        }

    def classify_plugin_variant(self, site_type: str, content: bytes) -> str:
        """
        分类插件具体变种
        返回: 'js_drpy', 'js_standalone', 'py_standalone', 'py_star'
        """
        variant = f"{site_type}_standalone" # Default
        
        try:
            text = content.decode('utf-8', errors='ignore')
            
            if site_type == 'js':
                # Check for drpy imports
                if 'drpy-core' in text or 'drpy2' in text or '//DRPY' in text:
                    variant = 'js_drpy'
            
            elif site_type == 'python':
                # Check for spider signatures
                if 'Spider' in text and 'getDependence' in text:
                    variant = 'py_t3' # T3/Spider system
                    
        except:
            pass
            
        return variant
    
    def test_plugin_urls(self, urls: List[str]) -> Dict[str, bool]:
        """
        测试插件中的 URL 是否可访问
        返回: {url: 是否可访问}
        """
        results = {}
        
        for url in urls[:10]:  # 只测试前10个
            try:
                req = urllib.request.Request(url, headers=self.session_headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    results[url] = response.status == 200
            except:
                results[url] = False
            
            time.sleep(0.1)  # 避免请求过快
        
        return results
    
    def validate_site(self, site: dict, base_url: str, download_dir: Path) -> Tuple[bool, dict]:
        """
        验证单个站点
        返回: (是否有效, 验证信息)
        """
        key = site.get('key', 'unknown')
        name = site.get('name', 'unknown')
        site_type = self.classify_site(site)
        
        info = {
            'key': key,
            'name': name,
            'type': site_type,
            'valid': False,
            'reason': '',
            'plugin_analysis': None
        }
        
        print(f"  验证: {name} ({site_type})")
        
        if site_type == 'api':
            # 测试 API
            valid, reason = self.test_api_site(site, base_url)
            info['valid'] = valid
            info['reason'] = reason
            print(f"    {'✓' if valid else '✗'} {reason}")
        
        elif site_type in ['js', 'python']:
            # 下载并分析插件
            api = site.get('api', '')
            ext = site.get('ext', '')
            
            # 构建完整 URL
            plugin_url = api if api.startswith('http') else urljoin(base_url, api)
            
            sub_dir = 'js' if site_type == 'js' else 'py'
            safe_key = re.sub(r'[^\w\-]', '_', key)
            
            # 尽量保持原文件名
            parsed_api = urlparse(plugin_url)
            filename = Path(parsed_api.path).name
            if not filename or not (filename.endswith('.js') or filename.endswith('.py')):
                file_ext = '.js' if site_type == 'js' else '.py'
                filename = f"{safe_key}{file_ext}"
                
            output_path = download_dir / sub_dir / filename
            
            success, content = self.download_plugin(plugin_url, output_path)
            
            if success and content:
                # [NEW] Detect Variant
                variant = self.classify_plugin_variant(site_type, content)
                info['variant'] = variant
                
                print(f"    ✓ 插件已下载 ({len(content)} bytes) [类型: {variant}]")
                
                # 分析插件
                if site_type == 'js':
                    analysis = self.analyze_js_plugin(content)
                    info['plugin_analysis'] = analysis
                    
                    if analysis['urls']:
                        print(f"    发现 {len(analysis['urls'])} 个 URL")
                        print(f"    涉及域名: {', '.join(analysis['domains'][:5])}")
                        
                        # 测试部分 URL
                        url_results = self.test_plugin_urls(analysis['urls'])
                        valid_count = sum(1 for v in url_results.values() if v)
                        total_count = len(url_results)
                        
                        if valid_count > 0:
                            info['valid'] = True
                            info['reason'] = f"插件可用，{valid_count}/{total_count} URL 可访问"
                            print(f"    ✓ {info['reason']}")
                        else:
                            info['valid'] = False
                            info['reason'] = f"插件内 URL 全部失效"
                            print(f"    ✗ {info['reason']}")
                    else:
                        # 没有找到 URL，可能是动态生成的
                        info['valid'] = True
                        info['reason'] = "插件已下载（无静态URL）"
                        print(f"    ⊙ {info['reason']}")
                else:
                    # Python 插件
                    info['valid'] = True
                    info['reason'] = "Python 插件已下载"
                    print(f"    ✓ {info['reason']}")
            
                # [CRITICAL] Rewrite config to point to local file (Enable Subdirectory Support)
                rel_path = f"./{sub_dir}/{filename}"
                site['api'] = rel_path
                
                # We will handle generic ext extraction later
                 
            else:
                info['valid'] = False
                info['reason'] = "插件下载失败"
                print(f"    ✗ {info['reason']}")
    
        elif site_type == 'jar':
            # JAR 插件 - 只有 csp_ 开头的才需要 jar
            api = site.get('api', '')
            
            if not api.startswith('csp_'):
                # 不是 csp_ 开头，不需要 jar
                info['valid'] = True
                info['reason'] = "非 CSP 插件，使用全局 JAR"
                print(f"    ✓ {info['reason']}")
            else:
                # csp_ 插件需要 jar
                jar_url = site.get('jar', '')
                
                if not jar_url:
                    # 没有指定 jar，使用全局的
                    info['valid'] = True
                    info['reason'] = "CSP 插件，使用全局 JAR"
                    print(f"    ✓ {info['reason']}")
                else:
                    # 有指定 jar，下载它
                    # 移除 md5 后缀
                    if ';md5;' in jar_url:
                        jar_url = jar_url.split(';md5;')[0]
                        
                    jar_url = jar_url if jar_url.startswith('http') else urljoin(base_url, jar_url)
                    
                    safe_key = re.sub(r'[^\w\-]', '_', key)
                    jar_parsed = urlparse(jar_url)
                    jar_name = Path(jar_parsed.path).name
                    if not jar_name.endswith('.jar'):
                        jar_name = f"{safe_key}.jar"
                    
                    output_path = download_dir / 'jar' / jar_name
                    
                    success, content = self.download_plugin(jar_url, output_path)
                    
                    if success:
                        info['valid'] = True
                        info['reason'] = f"JAR 已下载 ({len(content)} bytes)"
                        print(f"    ✓ {info['reason']}")
                        
                        # [CRITICAL] Rewrite config to point to local JAR
                        rel_jar_path = f"./jar/{output_path.name}"
                        site['jar'] = rel_jar_path

                    else:
                        info['valid'] = False
                        info['reason'] = "JAR 下载失败"
                        print(f"    ✗ {info['reason']}")
        
        else:
            info['valid'] = False
            info['reason'] = "未知类型"
            print(f"    ✗ {info['reason']}")
            
        # 统一处理附加内容的本地化
        if info['valid']:
            safe_key = re.sub(r'[^\w\-]', '_', key)
            
            # 1. ext 文件本地化
            ext_val = site.get('ext')
            if isinstance(ext_val, str) and (ext_val.startswith('./') or ext_val.startswith('../')):
                try:
                    ext_url = urljoin(base_url, ext_val)
                        
                    parsed_ext = urlparse(ext_url)
                    ext_fn = Path(parsed_ext.path).name
                    if not ext_fn:
                        ext_fn = f"{safe_key}_ext.txt"
                    
                    # 根据后缀选择目录
                    if ext_fn.endswith('.js'):
                        ext_sub = 'js'
                    elif ext_fn.endswith('.py'):
                        ext_sub = 'py'
                    else:
                        ext_sub = 'ext'
                    
                    # 下载文件
                    ext_out = download_dir / ext_sub / ext_fn
                    success_ext, _ = self.download_plugin(ext_url, ext_out)
                    if success_ext:
                        site['ext'] = f"./{ext_sub}/{ext_fn}"
                    else:
                        print(f"    ✗ ext 下载失败，移除相关站点")
                        info['valid'] = False
                        info['reason'] = "ext 文件下载失败或 404"
                except Exception as e:
                    print(f"    ✗ ext 处理异常，移除相关站点: {e}")
                    info['valid'] = False
                    info['reason'] = "ext 文件处理异常"
                    
            # 2. jar 文件本地化 (任何依赖独立 jar 的站)
            if info['valid']:
                jar_val = site.get('jar')
                if isinstance(jar_val, str) and (jar_val.startswith('http') or jar_val.startswith('./') or jar_val.startswith('../') or jar_val.startswith('//')):
                    try:
                        clean_jar = jar_val.split(';md5;')[0] if ';md5;' in jar_val else jar_val
                        if clean_jar.startswith('//'):
                            jar_url = 'https:' + clean_jar
                        elif clean_jar.startswith('./') or clean_jar.startswith('../'):
                            jar_url = urljoin(base_url, clean_jar)
                        else:
                            jar_url = clean_jar
                            
                        parsed_jar = urlparse(jar_url)
                        jar_fn = Path(parsed_jar.path).name
                        if not jar_fn.endswith('.jar'):
                            jar_fn = f"{safe_key}.jar"
                        jar_out = download_dir / 'jar' / jar_fn
                        success_jar, _ = self.download_plugin(jar_url, jar_out)
                        if success_jar:
                            site['jar'] = f"./jar/{jar_fn}"
                        else:
                            print(f"    ✗ 附加 jar 下载失败，移除相关站点")
                            info['valid'] = False
                            info['reason'] = "jar 文件下载失败或 404"
                    except Exception as e:
                        print(f"    ✗ 网盘或附加 jar 处理异常，移除相关站点: {e}")
                        info['valid'] = False
                        info['reason'] = "jar 文件处理异常"
        
        return info['valid'], info
    
    def validate_config(self, config_url: str, output_dir: Path, exclude_cloud: bool = False) -> dict:
        """
        验证完整配置
        返回: 验证报告
        """
        print(f"\n{'='*60}")
        print(f"验证配置: {config_url}")
        print(f"{'='*60}\n")
        
        # 下载配置
        config = self.download_config(config_url)
        if not config:
            return {'success': False, 'error': '配置下载失败'}
        
        # 提取基础 URL
        parsed_url = urlparse(config_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
        
        # 创建输出目录
        output_dir.mkdir(parents=True, exist_ok=True)
        download_dir = output_dir

        
        # 验证站点
        sites = config.get('sites', [])
        print(f"找到 {len(sites)} 个站点\n")
        
        valid_sites = []
        invalid_sites = []
        validation_details = []
        
        cloud_patterns = ['pan', 'share', 'wogg', 'wobg', 'moli', '阿里', '夸克', '网盘', 'alist']
        
        for site in sites:
            if exclude_cloud:
                name_lower = site.get('name', '').lower()
                api_lower = site.get('api', '').lower()
                if any(p in name_lower or p in api_lower for p in cloud_patterns):
                    invalid_sites.append(site)
                    info = {
                        'key': site.get('key', ''),
                        'name': site.get('name', 'unknown'),
                        'type': self.classify_site(site),
                        'valid': False,
                        'reason': '云盘/网盘源已被排除'
                    }
                    validation_details.append(info)
                    print(f"  验证: {info['name']} ({info['type']})")
                    print(f"    ✗ {info['reason']}")
                    continue
            
            valid, info = self.validate_site(site, base_url, download_dir)
            validation_details.append(info)
            
            if valid:
                valid_sites.append(site)
            else:
                invalid_sites.append(site)
            
            time.sleep(0.2)  # 避免请求过快
        
        # 生成清理后的配置
        clean_config = {
            'spider': config.get('spider', ''),
            'wallpaper': config.get('wallpaper', './bgwall.jpg'),
            'sites': valid_sites,
            'parses': config.get('parses', []),
            'lives': [live for live in config.get('lives', []) 
                     if isinstance(live, dict) and live.get('url', '').startswith('http')]
        }
        
        # 下载全局 spider jar
        spider_url = config.get('spider', '')
        if spider_url:
            clean_spider_url = spider_url.split(';md5;')[0] if ';md5;' in spider_url else spider_url
            if clean_spider_url.startswith('http') or clean_spider_url.startswith('//'):
                if clean_spider_url.startswith('//'):
                    clean_spider_url = 'https:' + clean_spider_url
                print(f"  下载全局 Spider JAR: {clean_spider_url}")
                spider_path = download_dir / 'jar' / 'spider.jar'
                success, content = self.download_plugin(clean_spider_url, spider_path)
                if success:
                    clean_config['spider'] = './jar/spider.jar'
                    print("    ✓ 全局 Spider 下载成功")
                else:
                    print("    ✗ 全局 Spider 下载失败，保留原连接")
                    clean_config['spider'] = spider_url
            else:
                clean_config['spider'] = spider_url
        
        # 保存清理后的配置
        clean_config_path = output_dir / 'config.json'
        with open(clean_config_path, 'w', encoding='utf-8') as f:
            json.dump(clean_config, f, ensure_ascii=False, indent=2)
        
        # 保存验证报告
        report = {
            'config_url': config_url,
            'total_sites': len(sites),
            'valid_sites': len(valid_sites),
            'invalid_sites': len(invalid_sites),
            'validation_details': validation_details,
            'clean_config_path': str(clean_config_path)
        }
        
        report_path = output_dir / 'validation_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        print(f"\n{'='*60}")
        print("验证完成")
        print(f"{'='*60}")
        print(f"总站点数: {len(sites)}")
        print(f"有效站点: {len(valid_sites)} ✓")
        print(f"无效站点: {len(invalid_sites)} ✗")
        print(f"\n清理后配置: {clean_config_path}")
        print(f"验证报告: {report_path}")
        
        return report

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能配置验证器")
    parser.add_argument('url', help='配置文件 URL')
    parser.add_argument('--output', default='smart_output', help='输出目录')
    parser.add_argument('--timeout', type=int, default=15, help='超时时间（秒）')
    
    args = parser.parse_args()
    
    validator = SmartValidator(timeout=args.timeout)
    output_dir = Path(args.output)
    
    try:
        report = validator.validate_config(args.url, output_dir)
        return 0 if report.get('valid_sites', 0) > 0 else 1
    except KeyboardInterrupt:
        print("\n\n已取消")
        return 1
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
