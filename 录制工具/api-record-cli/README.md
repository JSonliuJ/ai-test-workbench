# api-record

HTTP 接口采集工具，通过 Playwright CDP 录制浏览器网络请求并生成 Markdown 格式的 API 文档。

## 安装

```bash
pip install api-record
```

或从源码安装：

```bash
cd api-record
pip install -e .
```

## 使用方法

### 录制 API 文档

```bash
api-record record <url> [--output <dir>]
```

示例：

```bash
api-record record https://api.example.com
```

这将执行以下操作：
1. 打开 Chromium 浏览器
2. 导航到指定 URL
3. 注入一个悬浮的录制按钮
4. 捕获所有网络请求/响应
5. 点击录制按钮停止录制
6. 生成 Markdown 格式的 API 文档

### 输出

该工具在指定输出目录生成 `api-docs.md`，包含：

- API 端点列表（方法、URL）
- 请求头和请求体
- 响应状态码和响应体
- API 之间的依赖关系

## 环境要求

- Python 3.12+
- 已安装 Playwright 浏览器：`playwright install chromium`
