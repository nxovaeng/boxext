#!/usr/bin/env python3
"""
配置文件加载器

支持 YAML 和 JSON 格式的配置文件
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    """源配置"""
    name: str
    url: Optional[str] = None
    path: Optional[str] = None
    description: str = ""
    enabled: bool = True
    
    @property
    def is_online(self) -> bool:
        """是否为在线源"""
        return self.url is not None
    
    @property
    def source_path(self) -> str:
        """获取源路径（URL 或本地路径）"""
        return self.url if self.is_online else self.path


@dataclass
class ValidationConfig:
    """验证配置"""
    timeout: int = 15
    max_workers: int = 15
    retry_times: int = 2
    download_resources: bool = True
    deep_check: bool = True


@dataclass
class OutputConfig:
    """输出配置"""
    reports_dir: str = "reports"
    validated_dir: str = "validated_configs"
    download_dir: str = "downloaded_resources"
    formats: Dict[str, bool] = field(default_factory=lambda: {
        'text': True,
        'json': True,
        'html': True
    })


@dataclass
class GitHubPagesConfig:
    """GitHub Pages 配置"""
    enabled: bool = True
    generate_index: bool = True
    title: str = "TvBox 播放源检测报告"
    description: str = "自动化检测报告"


@dataclass
class Config:
    """完整配置"""
    sources: List[SourceConfig] = field(default_factory=list)
    local_sources: List[SourceConfig] = field(default_factory=list)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    github_pages: GitHubPagesConfig = field(default_factory=GitHubPagesConfig)
    
    @property
    def all_sources(self) -> List[SourceConfig]:
        """获取所有启用的源"""
        return [s for s in self.sources + self.local_sources if s.enabled]
    
    @property
    def online_sources(self) -> List[SourceConfig]:
        """获取所有启用的在线源"""
        return [s for s in self.sources if s.enabled]
    
    @property
    def local_sources_list(self) -> List[SourceConfig]:
        """获取所有启用的本地源"""
        return [s for s in self.local_sources if s.enabled]


class ConfigLoader:
    """配置加载器"""
    
    @staticmethod
    def load_yaml(config_path: str) -> Config:
        """加载 YAML 配置文件"""
        try:
            import yaml
        except ImportError:
            print("⚠️  PyYAML 未安装，尝试使用 JSON 格式")
            # 尝试转换为 JSON 格式
            json_path = config_path.replace('.yaml', '.json').replace('.yml', '.json')
            if os.path.exists(json_path):
                return ConfigLoader.load_json(json_path)
            raise ImportError("请安装 PyYAML: pip install pyyaml")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return ConfigLoader._parse_config(data)
    
    @staticmethod
    def load_json(config_path: str) -> Config:
        """加载 JSON 配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return ConfigLoader._parse_config(data)
    
    @staticmethod
    def _parse_config(data: Dict) -> Config:
        """解析配置数据"""
        # 解析源配置
        sources = []
        for source_data in data.get('sources', []):
            sources.append(SourceConfig(
                name=source_data['name'],
                url=source_data.get('url'),
                description=source_data.get('description', ''),
                enabled=source_data.get('enabled', True)
            ))
        
        # 解析本地源配置
        local_sources = []
        for source_data in data.get('local_sources', []):
            local_sources.append(SourceConfig(
                name=source_data['name'],
                path=source_data.get('path'),
                description=source_data.get('description', ''),
                enabled=source_data.get('enabled', True)
            ))
        
        # 解析验证配置
        validation_data = data.get('validation', {})
        validation = ValidationConfig(
            timeout=validation_data.get('timeout', 15),
            max_workers=validation_data.get('max_workers', 15),
            retry_times=validation_data.get('retry_times', 2),
            download_resources=validation_data.get('download_resources', True),
            deep_check=validation_data.get('deep_check', True)
        )
        
        # 解析输出配置
        output_data = data.get('output', {})
        output = OutputConfig(
            reports_dir=output_data.get('reports_dir', 'reports'),
            validated_dir=output_data.get('validated_dir', 'validated_configs'),
            download_dir=output_data.get('download_dir', 'downloaded_resources'),
            formats=output_data.get('formats', {
                'text': True,
                'json': True,
                'html': True
            })
        )
        
        # 解析 GitHub Pages 配置
        gh_pages_data = data.get('github_pages', {})
        github_pages = GitHubPagesConfig(
            enabled=gh_pages_data.get('enabled', True),
            generate_index=gh_pages_data.get('generate_index', True),
            title=gh_pages_data.get('title', 'TvBox 播放源检测报告'),
            description=gh_pages_data.get('description', '自动化检测报告')
        )
        
        return Config(
            sources=sources,
            local_sources=local_sources,
            validation=validation,
            output=output,
            github_pages=github_pages
        )
    
    @staticmethod
    def load(config_path: str = 'config.yaml') -> Config:
        """自动加载配置文件（支持 YAML 和 JSON）"""
        if not os.path.exists(config_path):
            print(f"⚠️  配置文件不存在: {config_path}")
            print("使用默认配置")
            return Config()
        
        # 根据文件扩展名选择加载方式
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            return ConfigLoader.load_yaml(config_path)
        elif config_path.endswith('.json'):
            return ConfigLoader.load_json(config_path)
        else:
            raise ValueError(f"不支持的配置文件格式: {config_path}")


def main():
    """测试配置加载"""
    import sys
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
    
    print(f"加载配置文件: {config_path}")
    config = ConfigLoader.load(config_path)
    
    print("\n在线源:")
    for source in config.online_sources:
        print(f"  - {source.name}: {source.url}")
    
    print("\n本地源:")
    for source in config.local_sources_list:
        print(f"  - {source.name}: {source.path}")
    
    print(f"\n验证配置:")
    print(f"  - 超时时间: {config.validation.timeout}s")
    print(f"  - 并发数: {config.validation.max_workers}")
    print(f"  - 下载资源: {config.validation.download_resources}")
    print(f"  - 深度检测: {config.validation.deep_check}")
    
    print(f"\n输出配置:")
    print(f"  - 报告目录: {config.output.reports_dir}")
    print(f"  - 验证目录: {config.output.validated_dir}")
    print(f"  - 下载目录: {config.output.download_dir}")


if __name__ == '__main__':
    main()
