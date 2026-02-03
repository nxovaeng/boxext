# TVBox 配置统一管理系统 (2026 版)

> **注意**: 本项目已完成重构。所有旧脚本和文档已归档至 `archive/` 目录。现在，您只需要使用一个工具：`unified_manager.py`。

## 🚀 项目概览

这是一个基于 2026 年最佳实践构建的 TVBox 配置管理系统。它集成了配置验证、资源下载、安全扫描和自动构建功能，旨在为您提供稳定、快速且安全的 TVBox 播放体验。

**核心功能:**
- **统一 CLI (`unified_manager.py`)**: 一个脚本搞定所有操作。
- **智能验证**: 深入分析 JS/Python 插件，不仅仅是简单的 API 连通性检查。
- **资源本地化**: 自动下载所有依赖资源 (JAR/JS/Py)，防止因源站失效导致的配置不可用。
- **安全扫描**: (新功能) 扫描下载的插件，检测潜在的恶意代码。
- **高级配置**: 一键生成包含广告过滤、DNS 优化的"高级版"配置。

## 🛠 快速开始

### 1. 验证配置源
检查 `config.json` 中配置的源是否有效。

```bash
# 验证所有源
python3 unified_manager.py validate

# 验证指定 URL (不读取配置文件)
python3 unified_manager.py validate --url https://example.com/config.json
```

### 2. 构建并发布
生成可直接部署的配置包。系统会自动清理无效源，并下载所有必要资源。

```bash
python3 unified_manager.py build
```

**输出目录**: `smart_output/merged/` (请部署此文件夹的内容)

### 3. 生成高级配置 (Premium)
生成包含去广告、DNS 优化和精选源的高质量配置。

```bash
python3 unified_manager.py premium
```

### 4. 安全扫描
扫描已下载的插件，查找可疑代码（如 `eval`, `exec`, 网络外联等）。

```bash
python3 unified_manager.py scan
```

### 5. 清理环境
删除临时构建文件和日志。

```bash
python3 unified_manager.py clean
```

## 📂 项目结构

```
boxext/
├── config.json              # 核心配置：定义源列表
├── unified_manager.py       # 🚀 统一管理工具 (入口脚本)
├── core/                    # 核心逻辑库 (验证器, 构建器)
├── MANUAL.md                # 📚 详细用户手册 (配置指南, 高级功能)
├── ANALYSIS_AND_RECOMMENDATION.md # 📈 现状分析与 2026 演进路线
├── archive/                 # 📦 归档的旧文件
└── publish_ready/           # ✅ 最终构建结果 (部署用)
```

## 🔮 未来规划 (2026+)

详情请参阅 [ANALYSIS_AND_RECOMMENDATION.md](ANALYSIS_AND_RECOMMENDATION.md)。
我们计划引入：
1. **AI 自动修复**: 使用大模型自动修复损坏的 JSON 配置路径。
2. **抗爬虫增强**: 升级验证核心为 `Playwright`，并模拟真实浏览器指纹 (JA3/JA4) 以绕过防火墙。
