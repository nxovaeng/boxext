# TVBox 资源配置

欢迎使用 TVBox 资源配置管理工具！

## 🚀 快速开始

### 订阅地址

----------纯API站点------------
```
https://box.zro.qzz.io/tvbox.json
```

==========聚合站点============
```
https://box.zro.qzz.io/tvbox.json
```


### 功能特点

- ✅ **智能筛选** - 自动过滤低质量站点
- ✅ **定时更新** - 每周自动构建发布
- ✅ **多源聚合** - 整合多个优质配置源
- ✅ **自定义插件** - 支持豆瓣热搜等扩展

## 📖 文档导航

| 文档 | 说明 |
|------|------|
| [使用手册](MANUAL.md) | 项目使用说明 |
| [DRPY代理指南](DRPY_PROXY_GUIDE.md) | DRPY 代理配置 |
| [配置分析](box_analysis.md) | TVBox 配置结构分析 |

## 📁 资源文件

| 文件 | 说明 |
|------|------|
| `tvbox.json` | 主配置文件 |
| `js/douban_hot_v2.js` | 豆瓣热搜插件 |

## 🔧 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 验证配置
python unified_manager.py validate

# 构建发布
python unified_manager.py build --output smart_output
```

## 📝 更新日志

查看 [GitHub Releases](https://github.com/your-repo/releases) 获取最新更新。
