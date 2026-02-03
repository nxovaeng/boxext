# TVBox 配置管理系统 - 用户手册 (2026 版)

## 1. 简介
本项目是基于 **2026 年最佳实践** 构建的 TVBox 配置管理系统。我们为您提供了一套完整的工具链，用于验证、构建和优化您的 TVBox 配置文件 (json, js, py)。

**核心理念:**
*   **统一:** 一个脚本 (`unified_manager.py`) 搞定验证、下载、清理、构建。
*   **安全:** 本地下载并校验资源完整性，提供安全扫描功能。
*   **智能:** 自动分析插件依赖，去伪存真。
*   **稳定:** 自动生成本地发布目录，源站失效也不会导致您的配置不可用。

---

## 2. 快速入门

### 2.1 基础验证
验证您的配置文件是否有效。

```bash
# 读取 config.json 中的所有源并验证
python3 unified_manager.py validate

# 仅验证指定的 URL
python3 unified_manager.py validate --url https://raw.githubusercontent.com/user/tvbox/main/config.json
```

### 2.2 构建并发布 (Build & Publish)
此命令会自动完成以下步骤：
1.  验证所有启用的源。
2.  下载所有 `site.api`, `spider.jar`, `ext` 中的 JS/Python 文件。
3.  自动分析 JS/Python 插件中引用的隐式依赖并尝试预下载。
4.  生成去重的、可部署的配置文件。

```bash
python3 unified_manager.py build
```

**输出目录**: `smart_output/merged/`

**如何使用:**
1.  将 `smart_output/merged/` 目录上传到您的 Web 服务器、CDN 或 GitHub Pages。
2.  在 TVBox 中输入该地址即可使用。

**本地测试:**
```bash
cd smart_output/merged
python3 -m http.server 8000
# 访问 http://localhost:8000/config.json
```

### 2.3 生成高级配置 (Premium)
自动生成针对 **去广告**、**DNS 优化** 和 **高质量源筛选** 的特制配置。

```bash
python3 unified_manager.py premium
```
> **注意:** 需要您的系统环境支持相关Python库 (requests, beautifulsoup4 等)。

---

## 3. 配置指南

### 3.1 `config.json` 格式
这是您管理源的唯一入口。

```json
{
  "sources": [
    {
      "name": "示例源1",
      "url": "https://example.com/api/config.json",
      "enabled": true
    },
    {
      "name": "本地源",
      "url": "file:///path/to/local.json",
      "enabled": false
    }
  ],
  "validation": {
    "timeout": 15,
    "max_workers": 10
  }
}
```

### 3.2 高级功能 (Premium Features)
在 `python3 unified_manager.py premium` 命令中，系统会自动应用以下优化：

*   **智能过滤:** 去除已知的低质量或失效源。
*   **广告屏蔽:** 自动合并 58+ 条广告过滤规则，包括恶意 TS 切片和常见广告域名。
*   **DNS 优化:** 启用 DoH (DNS over HTTPS)，推荐使用 Google DNS 或 Cloudflare DNS 提升解析速度和隐私。
*   **解码优化:** 根据源类型推荐软解/硬解配置。

---

## 4. 技术原理 (Technical Reference)
*基于对 TVBox 源码的深度分析，帮助您理解配置背后的机制。*

### 4.1 插件加载机制
TVBox 采用**插件化架构**，根据 `api` 字段的前缀或后缀调用不同的加载器：

1.  **JarLoader (Java/JAR)**
    *   **触发条件**: `api` 以 `csp_` 开头 (如 `csp_XBPQ`) 或指定了 `jar` 字段。
    *   **原理**: 使用 Android `DexClassLoader` 动态加载 JAR/DEX 文件。支持 `com.github.catvod.spider.Init` 初始化。
    *   **特点**: 性能最高，支持 MD5 完整性校验 (防止篡改)。
    
2.  **JsLoader (JavaScript)**
    *   **触发条件**: `api` 包含 `.js`。
    *   **原理**: 基于 **QuickJS** 引擎执行。支持 ES6 模块和 Base64 编码 (以 `//bb` 或 `//DRPY` 开头)。
    *   **特点**: 更新灵活，支持热修复，但性能略低于 Java。

3.  **PyLoader (Python)**
    *   **触发条件**: `api` 包含 `.py`。
    *   **原理**: 通过 `pyramid` 模块提供的 Python 环境执行。
    *   **特点**: 适合移植爬虫，库支持丰富。

### 4.2 核心配置详解
`config.json` 中的字段直接映射到 App 的 Java Bean：

*   **type**: 站点类型
    *   `0`: 影视 (CMS/XML)
    *   `1`: 直播 (IPTV)
    *   `2`: 解析 (Parse)
    *   `3`: 爬虫 (Spider - 核心类型)
    *   `4`: XPath
*   **ext**: 扩展参数
    *   传递给 Spider `init` 方法的参数。可以是 JSON 字符串、Base64 或远程 URL。
*   **style**:用于指定UI布局样式 (如 `{"type":"rect"}` 矩形海报)。

### 4.3 缓存与安全
*   **缓存**: App 使用 Hawk 库和文件缓存。配置和 JAR 都有 MD5 校验机制。
*   **网络**: 底层使用 OkHttp，我们的 `unified_manager.py` 生成的配置优化了 DoH，利用 OkHttp 的 DNS over HTTPS 能力抗 DNS 污染。

---

## 5. 故障排查

**Q: 验证失败 ("Validation Failed")**
A: 请检查网络。部分源可能会屏蔽非家庭宽带 IP (如服务器 IP)，您可以尝试在本地电脑运行或使用代理。

**Q: 缺少依赖 ("Missing Dependencies")**
A: 请确保已安装所有 Python 依赖：`pip install -r requirements.txt`。

**Q: 导入错误 ("ImportError")**
A: 请在 `boxext` 根目录下运行脚本，不要进入 `core/` 目录运行。

**Q: 为什么生成的配置无法播放？**
A:
1.  检查生成的 `jar` 目录是否有文件。
2.  确保您的服务器能够正确响应 ".json", ".jar", ".js" 文件的请求 (MIME Type)。

---

*本文档替代了旧版的 `QUICK_REFERENCE.md`, `USAGE_GUIDE.md`, 和 `QUICK_START.md`。*
