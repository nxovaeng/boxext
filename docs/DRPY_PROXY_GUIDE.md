# DrPy Local Proxy Deployment Guide

## 1. 什么是 `127.0.0.1:9978`?
在 `drpy_js` 插件中，您经常会看到 `127.0.0.1:9978`。这是一个**本地代理服务 (CMS Proxy)**。
*   **作用**: 它负责处理复杂的加密解密、HTML 解析 (PyQuery/XPath) 和跨域请求反向代理，弥补了纯 JS 环境能力的不足。
*   **来源**: 在 TVBox APP 运行时，APP 内部会启动这个服务。但在 PC 端验证或使用离线包时，您需要手动运行这个服务。

## 2. 如何部署服务?

### 方案 A: 使用 Python (类似于 `hipy-server`)
这是最通用的方法，模拟 TVBox 的 Python 后端。

1.  **准备环境**:
    *   安装 Python 3.8+
    *   安装依赖: `pip install flask requests lxm gunicorn`

2.  **创建服务器脚本 `proxy_server.py`**:
    ```python
    from flask import Flask, request, Response
    import requests

    app = Flask(__name__)

    @app.route('/proxy')
    def proxy():
        url = request.args.get('url')
        if not url: return "Missing URL", 400
        # 简单转发 (生产环境需完善 Header处理)
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            return Response(resp.content, resp.status_code, dict(resp.headers))
        except Exception as e:
            return str(e), 500

    @app.route('/cms')
    def cms():
        # 这里需要实现 CMS 接口逻辑 (通常比较复杂，建议使用现成项目)
        return "CMS Mock"

    if __name__ == '__main__':
        app.run(host='127.0.0.1', port=9978)
    ```

3.  **运行**: `python proxy_server.py`

### 方案 B: 使用 Docker (推荐)
社区有成熟的 Docker 镜像 (如 `als-server` 或 `hipy-server`)。

```bash
docker run -d -p 9978:9978 --name tvbox-proxy link/to/image
```
*(注: 请在 Docker Hub 搜索 "tvbox proxy" 或 "hipy" 获取最新镜像)*

### 方案 C: 仅验证 (忽略)
如果您只是验证配置格式，而不是真的要播放视频，可以在 `SmartValidator` 中忽略此地址 (我们已通过代码更新实现了这一点，报告中不再报错)。

## 3. 在配置中使用
如果您的服务部署在公网 IP 或局域网其他机器 (如 NAS)，请修改 JS 插件中的地址：
*   **原代码**: `return "http://127.0.0.1:9978/proxy?do=js"`
*   **修改后**: `return "http://192.168.1.100:9978/proxy?do=js"`

## 4. 常见项目参考
要获得完整的 9978 服务能力 (包含 OCR、加密)，建议参考以下开源项目：
*   [HiPy-Server](https://github.com/hjdhnx/hipy-server) (Python)
*   [CatVodOpen](https://github.com/CatVod/CatVodOpen) (Java/Android)

## 5. TVBox APP 运行机制 (FAQ)

**Q: 在 TVBox APP (安卓端) 运行时，我需要手动开启这个服务吗？**

**A: 不需要。** 
TVBox APP 内部集成了 `drpy` 的 Python 环境（或 Java 模拟层）。
1.  **自动启动**: 当 APP 启动时，它会自动在后台运行一个本地代理服务 (通常监听 9978 端口)。
2.  **自动配置**: 您的配置文件中只要写 `http://127.0.0.1:9978/...`，APP 内部的 WebView 就能自动请求到这个内置服务。
3.  **开发注意**: 本文档介绍的 "部署指南" 主要是为了让您在 **电脑 (PC/Mac/Linux)** 上测试插件，或者在 **NAS/服务器** 上集中部署时使用。
