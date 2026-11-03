# ai-test-workbench

基于 AI 的测试工作台 —— 覆盖「需求 → 测试点 → 测试用例 → 测试文档 → 审核」全链路的技能与工具集。

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
├── .claude/skills/              # Claude Code 技能（24 个，含 7 个测试技能）
├── .trae/skills/                # Trae 技能
│   ├── web-standards/           #   纯原生 HTML/CSS/JS 编码规范
│   └── test-plan-generator/     #   测试方案生成器
├── .claude/doc/                 # 测试过程产物
│   ├── 01-需求/                 #   需求文档、接口文档、测试点
│   ├── 02-测试/                 #   测试用例（MD / Excel）
│   └── company-test-document/   #   企业测试文档、审核报告
├── project-demo/                # 前端示例
│   ├── login_page/              #   原生 HTML/CSS/JS 登录页
│   └── todo-app/                #   Vue 3 + Vite + Tailwind 待办应用
├── .mcp.json                    # MCP 服务配置：MySQL + Playwright
└── 环境平台搭建.md               # Dify / Claude Code / NVM 环境部署笔记
```

---

## 测试技能详解

`.claude/skills/` 下 24 个技能中有 7 个面向测试，按用途分为四类：**需求拆解 → 测试点/用例生成 → 测试文档产出 → 文档审核**。

### 一、需求拆解

#### `req-doc-testpoint-generator` —— 需求文档 → WEB 测试点

| 项 | 说明 |
|---|---|
| **输入** | `{项目根目录}/01-需求/` 下的需求 MD 文档（仅读已拆分完毕的 MD） |
| **输出** | `{项目根目录}/02-测试/测试点分析/`，按需求文档一一对应的同名 MD |
| **核心能力** | 自动拆解需求 → 区分「全局公共模块」与「独立功能模块」→ 输出结构化测试点 |

工作规则（技能内强制约束）：
- 仅以 `01-需求/` 为数据源，**禁止**解读目录外文件、**禁止**篡改需求原文、**禁止**新增需求外的测试点
- 文档编号以 `4.` 开头（含所有 `4.x` 子模块）判定为功能模块，例：`4.1用户登录.md` → 输出 `用户登录.md`
- 文件名以固定编号开头的一批文档直接忽略（如 `01`~`03` 类编号文件）

**触发语**：`生成测试点`、`WEB 测试点分析`、`从需求拆解测试点`、`功能模块测试点`

---

### 二、测试点与用例生成

#### `api-testpoint-generator` —— Swagger/OpenAPI → 接口测试点

| 项 | 说明 |
|---|---|
| **输入** | Swagger JSON、OpenAPI 规范或接口文档 |
| **输出** | 标准 API 接口测试点文档（含请求参数、响应字段、测试点清单） |
| **配套脚本** | `scripts/swagger_parser.py`、`scripts/generate-uuid.py` |

关键规则：
- 接口名称取 `paths.[path].summary`，格式为 `中文摘要_英文路径`（如 `获取余额_getBalance`）
- 嵌套对象**递归展开**，字段路径用 `.` 分隔（`user.address.city`）
- 有 `example`/`examples` 则格式化为 JSON 输出；无则输出 `// 待补充：请提供真实数据` 占位
- 正常响应示例取 `responses.200.examples`/`example`；录制批次未捕获到时输出 `// 待补充：录制批次中未捕获到正常响应体`
- 输出模板字段不可增删

**触发语**：`生成接口测试点`、`接口文档编写`、`从 Swagger 生成测试文档`、`API 测试用例准备`

#### `api-case-generator` —— 接口文档 → 可执行测试用例

| 项 | 说明 |
|---|---|
| **输入** | 接口文档（Markdown / Swagger JSON / API 说明文档） |
| **输出** | ① `{接口名}_测试用例.md` ② 同名 Excel（`openpyxl` 可选） |
| **配套脚本** | `scripts/generate-uuid.py`、`scripts/xlsx_from_json.py` |
| **参考库** | `references/` 下的用例规范 |

**触发语**：`生成测试用例`、`接口测试`、`API 测试用例编写`、`测试用例设计`

---

### 三、测试文档产出

#### `company-test-doc` —— 企业内部轻量化测试文档

支持 **8 种**文档类型。其中「测试计划」「测试报告」的**内核严格遵循国标**（章节名称由企业自定义），其余 6 种为企业内部过程管理文档（**无国家强制目录**，按企业规范自定义结构）：

| # | 文档类型 | 目录依据 |
|---|---|---|
| 1 | 测试计划 | 内核对标国标 |
| 2 | 测试报告 | 内核对标国标 |
| 3 | 测试方案 | 企业自定义 |
| 4 | 测试周报 | 企业自定义 |
| 5 | 测试用例评审纪要 | 企业自定义 |
| 6 | 缺陷分析报告 | 企业自定义 |
| 7 | 测试启动会备忘 | 企业自定义 |
| 8 | 线上漏测复盘报告 | 企业自定义 |

交互流程：选择文档类型 → 逐章节引导填写 → 汇总生成。

**触发语**：`测试计划`、`测试报告`、`测试周报`、`缺陷复盘`、`上线审批`，或任何版本迭代的质量保障文档

#### `test-doc` —— 国标合规测试计划

严格遵循 **GB/T 8567-2006《计算机软件文档编制规范》** 与 **GB/T 9386-2008《计算机软件测试文档规范》**，用于企业资质审核、项目合规验收、招投标资料提交。

- **固定文档结构**：按国标章节顺序，不可增删
- **写作风格**：严谨、客观、正式、合规，杜绝口语化、模糊化、绝对化表述
- **交互流程**：确认文档类型 → 逐章节引导填写 → 汇总生成完整文档
- **章节参考库**：内置各章节填写示例（1.1 标识 / 1.2 系统概述 / 1.3 文档概述 / 1.4 与其他计划的关系 …）

**触发语**：`国标测试计划`、`软件测试计划编制`、`合规性测试文档`、`资质验收测试文档`

---

### 四、文档审核

#### `test-audit` —— 测试文档合规审核

对已有测试文档做合规校验，自动识别文档类型后套用对应审核清单，兼具「国标对外审核」与「企业内部审核」双重标准。

输出结构固定为四段：
1. **逐项校验结果**
2. **存在问题清单**
3. **精准修改建议**
4. **最终审核结论**

**触发语**：`审核测试文档`、`文档合规检查`、`国标审核`、`测试文档评审`

---

### 五、辅助验证

#### `webapp-testing` —— 本地 Web 应用自动化验证

基于 Playwright 的 Python 脚本工具集，用于验证前端功能、排查 UI 行为、抓取浏览器截图与控制台日志。

- `scripts/with_server.py` —— 统一管理本地服务生命周期（支持多服务并行）
- **使用约定**：先跑 `--help` 看用法，脚本按黑盒调用，**不要**直接读源码（文件体积大，会污染上下文）
- **推荐模式**：先侦察（snapshot / console / network）再执行操作，而非盲目试错

---

### 技能协作链路

```
01-需求/需求文档
   │
   ├─ req-doc-testpoint-generator ──→ 02-测试/测试点分析/     （WEB 测试点）
   │
   ├─ 录制工具（web-record / api-record）
   │      └─ api-testpoint-generator ──→ API 接口测试点文档
   │
   └─ api-case-generator ────────────→ 02-测试/{接口名}_测试用例.md + .xlsx
                                            │
                                            ▼
                       company-test-doc / test-doc ──→ 测试计划、测试报告
                                            │
                                            ▼
                                          test-audit ──→ 审核报告
```

---

## 其他技能

| 技能 | 用途 |
|---|---|
| `web-standards` | 纯原生 HTML/CSS/JS 编码规范，禁 CSS 框架与图标库 |
| `test-plan-generator` | 测试方案生成器，10 个设计维度 + 固定 10 节输出结构 |
| `frontend-design` | 生产级前端界面设计 |
| `docx` / `pptx` / `xlsx` | 办公文档创建、编辑与解析 |
| `pdf` | PDF 提取、合并拆分、表单填充 |
| `mcp-builder` | 创建 MCP 服务器 |
| `skill-creator` | 创建或改造技能 |
| `canvas-design` / `algorithmic-art` / `theme-factory` | 视觉内容生成 |
| `doc-coauthoring` / `internal-comms` | 文档协作与内部沟通写作 |
| `web-artifacts-builder` | 复杂 HTML artifact 构建 |
| `slack-gif-creator` | Slack GIF 制作 |
| `brand-guidelines` | Anthropic 品牌规范应用 |
| `claude-api` | Claude API 应用开发与优化 |

> `.claude/skills/` 与 `.trae/skills/` 存在部分同名技能（`web-standards`、`test-plan-generator`、`docx` 等）。`.claude/` 供 `claude` 命令使用，`.trae/` 供 Trae IDE 使用，按需各取所需。

---

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

### 3. 生成测试点与用例

用 `req-doc-testpoint-generator` 从需求出 WEB 测试点，用 `api-testpoint-generator` + `api-case-generator` 从接口文档出用例。

### 4. 产出与审核文档

`company-test-doc` 出内部文档，`test-doc` 出国标测试计划，`test-audit` 做合规审核。

---

## MCP 服务

`.mcp.json` 已配置两个服务：

| 服务 | 包 | 用途 |
|---|---|---|
| `mysql` | `@kevinwatt/mysql-mcp` | 数据库查询、DDL 执行、表结构探查 |
| `playwright` | `@playwright/mcp` | 浏览器自动化、页面快照 |

---

## 说明

- `.claude/skills/.git.bak/` 是从 gitee 克隆 skills 仓库时残留的原始 git 目录备份，已被 `.gitignore` 排除
- `.venv/`、`node_modules/`、`.playwright-mcp/` 等本地环境与产物目录均不纳入版本管理
