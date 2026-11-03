# ai-api-test-workbench

基于 AI 的接口测试工作台 —— 从需求文档到接口录制、测试点生成、测试计划与测试报告的完整链路工具集。

## 目录结构

```
├── 录制工具/                    # 接口/流量录制 CLI（Python + Playwright + CDP）
│   ├── web-record-cli/          #   Web 侧录制：抓取 XHR/Fetch，生成 API 文档
│   └── api-record-cli/          #   接口侧录制
├── 提示词参考/                  # 提示词模板库
│   ├── API测试点生成提示词/      #   接口测试点生成
│   ├── AI录制测试点分析-API/     #   录制结果 → 测试点
│   ├── AI录制测试点分析-WEB/     #   录制结果 → 测试点
│   └── API生成接口测试用例/      #   测试点 → 测试用例
├── .trae/skills/                # Trae 技能
│   ├── web-standards/           #   纯原生 HTML/CSS/JS 编码规范
│   └── test-plan-generator/     #   测试方案生成器
├── .claude/                     # Claude Code 配置与产物
│   ├── skills/                  #   21 个技能（docx/pptx/xlsx/frontend-design 等）
│   └── doc/                     #   需求文档、测试计划、测试报告
├── project-demo/                # 前端示例
│   ├── login_page/              #   原生 HTML/CSS/JS 登录页
│   └── todo-app/                #   Vue 3 + Vite + Tailwind 待办应用
├── .mcp.json                    # MCP 服务配置：MySQL + Playwright
└── 环境平台搭建.md               # Dify / Claude Code / NVM 环境部署笔记
```

## 快速开始

### 1. 准备环境

```powershell
# 创建并激活虚拟环境
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"

# 安装录制工具
pip install -e ".\录制工具\web-record-cli"
pip install -e ".\录制工具\api-record-cli"
```

> 浏览器二进制单独安装（国内建议走镜像源）：
> ```powershell
> $env:PLAYWRIGHT_DOWNLOAD_HOST = "https://npmmirror.com/mirrors/playwright"
> playwright install chromium
> ```

### 2. 录制接口

```powershell
web-record record "https://www.example.com" -o ".\需求采集"
```

浏览器弹出后操作页面，点击悬浮的 PCR 按钮停止录制，工具会输出接口文档。

### 3. 生成测试点与测试方案

使用 `提示词参考/` 下的模板，配合 `test-plan-generator` 技能产出测试方案、测试计划与测试报告。

## MCP 服务

`.mcp.json` 已配置两个服务：

| 服务 | 包 | 用途 |
|---|---|---|
| `mysql` | `@kevinwatt/mysql-mcp` | 数据库查询、DDL 执行、表结构探查 |
| `playwright` | `@playwright/mcp` | 浏览器自动化、页面快照 |

## 技能

`.trae/skills/` 与 `.claude/skills/` 下的技能可被对应 AI 工具直接加载：

- **web-standards** —— 纯原生 HTML/CSS/JS 编码规范，禁框架与图标库
- **test-plan-generator** —— 测试方案生成器，10 个设计维度 + 固定输出结构
- **frontend-design** —— 生产级前端界面设计
- **docx / pptx / xlsx** —— 办公文档处理

## 说明

- `.claude/skills/.git.bak/` 是从 gitee 克隆 skills 仓库时残留的原始 git 目录备份，已被 `.gitignore` 排除
- `.venv/`、`node_modules/`、`.playwright-mcp/` 等本地环境与产物目录均不纳入版本管理
