# TVBox 智能构建结果

## 构建摘要

- **总站点数**: 100
- **解析器数**: 38
- **直播源数**: 19
- **插件文件**: 106

## 源验证结果

### qist-jsm

- URL: https://qist.wyfc.qzz.io/jsm.json
- 有效站点: 183/183
- 详细报告: `qist-jsm/validation_report.json`

### qist-xiaosa

- URL: https://raw.githubusercontent.com/qist/tvbox/refs/heads/master/xiaosa/api.json
- 有效站点: 146/146
- 详细报告: `qist-xiaosa/validation_report.json`

### cluntop-box

- URL: https://clun.top/box.json
- 有效站点: 105/119
- 详细报告: `cluntop-box/validation_report.json`


## 使用方法

### 本地测试

```bash
cd smart_output/merged
python3 -m http.server 8000
```

访问: `http://localhost:8000/config.json`

### 部署

将 `smart_output/merged` 目录部署到任意 HTTP 服务器。

### 在 TVBox 中使用

配置地址: `http://your-domain/config.json`

## 目录结构

```
smart_output/merged/
├── config.json      # 主配置文件
├── js/              # JavaScript 插件
├── py/              # Python 插件
└── jar/             # JAR 插件
```

## 注意事项

1. 所有站点都经过验证，只保留有效的
2. 插件文件已下载并分析
3. 定期重新构建以更新配置
