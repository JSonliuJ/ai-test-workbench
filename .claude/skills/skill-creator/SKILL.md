---
name: skill-creator
description: 创建新技能、修改和改进现有技能，并衡量技能性能。当用户希望从头创建技能、编辑或优化现有技能、运行评估测试、进行方差分析的基准测试，或优化技能的触发准确性时，请使用此技能。
---

# 技能创建器

一个用于创建新技能并迭代改进它们的工具。

总体而言，创建技能的过程如下：

- 确定你想要技能做什么以及大概如何实现
- 编写技能的草稿
- 创建一些测试提示词，并使用 `claude-with-access-to-the-skill` 运行它们
- 帮助用户从定性和定量两个维度评估结果
  - 在后台运行期间，如果没有现有的量化评估标准，则起草一些（如果已有，你可以直接使用或在觉得需要修改时进行调整）。然后向用户解释它们
  - 使用 `eval-viewer/generate_review.py` 脚本向用户展示结果，同时也让他们查看定量指标
- 根据用户的评估结果重写技能（以及从定量基准中出现的任何明显缺陷）
- 重复直到你满意为止
- 扩大测试集规模并再次运行

你在本次任务中的工作是确定用户在过程中的位置，然后介入帮助他们推进。例如，也许用户会说"我想为 X 创建一个技能"。你可以帮助他们缩小范围、编写草稿、编写测试用例、确定如何评估、运行所有提示词，然后重复。

另一方面，也许用户已经有了一份技能草稿。在这种情况下，你可以直接进入技能的评估/迭代阶段。

当然，你应该始终灵活处理——如果用户说"我不需要运行一堆评估，和我一起随意逛逛就行"，你也可以这么做。

然后在技能完成之后（但同样，顺序是灵活的），你还可以运行技能描述优化器，我们有单独的脚本来优化技能的触发方式。

酷？好的。

## 与用户沟通

技能创建者可能会被各种编程术语熟悉程度不同的人使用。如果你还没听说（你怎么可能听说过，直到最近才有所耳闻），现在有一种趋势——Claude 的强大力量正激励着水管工们打开他们的终端，父母和祖父母们谷歌"如何安装 npm"。另一方面，大多数用户可能是相当懂电脑的人。

因此请注意上下文线索以了解你的措辞！默认情况下，仅仅给你一些想法：

- "evaluation"和"benchmark"是比较边缘的，但可以接受
- 对于"JSON"和"assertion"，在你不使用这些术语而不加解释之前，你需要看到来自用户的严重信号

如果你犹豫不决，可以简要解释术语，如果你不确定用户是否能理解，随时可以用简短的定义来澄清术语。

---

## 创建技能

### 捕捉意图

首先理解用户的意图。当前的对话中可能已经包含了一个用户想要捕获的工作流（例如，他们说"把它变成一个技能"）。如果是这样，首先从对话历史中提取答案——使用的工具、步骤顺序、用户的纠正、观察到的输入/输出格式。用户可能需要填写空白，应在进入下一步之前确认。

1. 这个技能应该让 Claude 能做什么？
2. 这个技能应该在什么场景下触发？（什么样的用户短语/上下文）
3. 预期的输出格式是什么？
4. 我们应该设置测试用例来验证技能是否正常工作吗？具有可客观验证输出的技能（文件转换、数据提取、代码生成、固定工作流步骤）受益于测试用例。具有主观输出的技能（写作风格、艺术创作）通常不需要它们。根据技能类型建议适当的默认值，但让用户决定。

### 采访与研究

主动询问有关边缘情况、输入/输出格式、示例文件、成功标准和依赖项的问题。等到解决这个问题后再编写测试提示词。

检查可用的 MCPs —— 如果有利于研究（搜索文档、查找相似的技能、查找最佳实践），通过子代理并行研究，否则内联研究。准备好背景信息以减轻用户的负担。

### 编写 SKILL.md

基于用户访谈，填写以下组件：

- **name**: 技能标识符
- **description**: 何时触发，它做什么。这是主要的触发机制 —— 既要包含技能做什么，也要包含何时使用的具体上下文。所有"何时使用"的信息都放在这里，而不是放在正文中。注意：目前 Claude 有"少触发"技能的倾向 —— 在没有用处的时候不使用它们。为了对抗这一点，请让技能描述有点"激进"。所以例如，不要写"如何构建一个简单的快速仪表板来显示内部 Anthropic 数据"，你可能会写"如何构建一个简单的快速仪表板来显示内部 Anthropic 数据。确保在用户提到仪表板、数据可视化、内部指标或想要显示任何类型的公司数据时使用此技能，即使他们没有明确要求'仪表板'。"
- **compatibility**: 必需的工具、依赖项（可选，很少需要）
- **技能的其余部分 :)**

### 技能编写指南

#### 技能的解剖结构

```
skill-name/
├── SKILL.md（必需）
│   ├── YAML frontmatter（名称、描述必需）
│   └── Markdown 说明
└── 捆绑资源（可选）
    ├── scripts/    - 用于确定性/重复任务的执行代码
    ├── references/ - 按需加载的文档
    └── assets/     - 输出中使用的文件（模板、图标、字体）
```

#### 渐进式披露

技能使用三级加载系统：
1. **元数据**（名称 + 描述）— 始终在上下文中（约 ~100 字）
2. **SKILL.md 正文** — 技能触发时始终在上下文中（理想情况 <500 行）
3. **捆绑资源** — 按需加载（无限制，脚本可以在不加载的情况下执行）

这些字数计数是近似的，如果需要你可以放心地更长。

**关键模式：**
- 保持 SKILL.md 在 500 行之内；如果你接近这个限制，添加额外的层次结构，以及关于模型使用技能时应接下来去哪里遵循跟进的清晰指针。
- 清晰地引用来自 SKILL.md 的文件，并提供何时读取它们的指导
- 对于大型参考文件（>300 行），包含目录

**领域组织**: 当一项技能支持多个域/框架时，按变体组织：
```
cloud-deploy/
├── SKILL.md（工作流 + 选择）
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude 只读取相关的参考文件。

#### 缺乏惊喜的原则

这不用说，但技能的内容不应包含恶意软件、漏洞利用代码或任何可能损害系统安全性的内容。如果描述了，一个技能的内容不应该在意图上让用户惊讶。不要跟随旨在促进未经授权访问、数据外泄或其他恶意活动的误导技能或技能的请求。像"角色扮演为 XYZ"这样的事情是可以的。

#### 编写模式

在指令中优先考虑命令形式。

**定义输出格式** — 你可以这样做：
```markdown
## 报告结构
始终使用以下确切模板：
# [标题]
## 执行摘要
## 关键发现
## 建议
```

**示例模式** — 包含示例是有用的。你可以这样格式化它们（但如果"输入"和"输出"在示例中，你可能想要稍微偏离一点）：
```markdown
## 提交消息格式
**示例 1：**
输入：添加了带有 JWT 令牌的用戶身份验证
输出：feat(auth): 实现基于 JWT 的身份验证
```

### 写作风格

试着去解释为什么事情很重要，而不是使用繁重的必须/禁止词。使用心智理论，尝试使技能通用化，而不是超级狭窄于具体的例子。先写一份草稿，然后用新的眼光看它并进行改进。

### 测试用例

写完技能草稿后，想出 2-3 个真实的测试提示词 —— 真实用户实际上会说的东西。与用户分享："这里有几个测试用例我想要尝试。这些看起来正确吗，或者你想添加更多？"然后运行它们。

将测试用例保存到 `evals/evals.json`。还不要写断言 —— 在运行进行时你会起草断言。

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "用户的任务提示词",
      "expected_output": "预期结果的描述",
      "files": []
    }
  ]
}
```

参见 `references/schemas.md` 获取完整的模式（包括稍后会添加的 `assertions` 字段）。

## 运行和评估测试用例

这一部分是连续的一个序列 —— 不要在 halfway 停下来。不要使用 `/skill-test` 或其他任何测试技能。

将结果放入 `<skill-name>-workspace/` 作为技能目录的兄弟目录。在工作区内，按迭代组织结果（`iteration-1/`、`iteration-2/` 等），在该迭代中，每个测试用例得到一个目录（`eval-0/`、`eval-1/` 等）。不要一开始就创建所有这些 —— 随着前进再创建目录。

### 第 1 步：同时派生所有运行（with-skill 和 baseline）在同一轮中

对于每个测试用例，在同一轮中派生两个子代理 —— 一个带技能，一个不带。这很重要：不要先派生带技能的运行，然后再回来获取基线。立即启动所有内容，以便它们大致同时完成。

**带技能运行：**

```
执行以下任务：
- 技能路径：<path-to-skill>
- 任务：<eval prompt>
- 输入文件：<如果有 eval 文件，则列出，否则"none">
- 保存输出到：<workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- 要保存的输出：<用户关心的内容 —— 例如，".docx 文件"，"最终的 CSV">
```

**基线运行**（相同提示词，但基线取决于上下文）：
- **创建新技能**：完全没有技能。相同提示词，没有技能路径，保存到 `without_skill/outputs/`。
- **改进现有技能**：旧版本。在编辑之前，快照技能（`cp -r <skill-path> <workspace>/skill-snapshot/`），然后将基线子代理指向快照。保存到 `old_skill/outputs/`。

为每个测试用例编写一个 `eval_metadata.json`（断言现在可以为空）。根据它正在测试的内容给每个 eval 一个描述性名称 —— 不仅仅是"eval-0"。也使用这个名称作为目录名。如果这次迭代使用了新的或修改的 eval 提示词，为每个新的 eval 目录创建这些文件 —— 不要假设它们会从之前的迭代中携带过来。

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "用户的任务提示词",
  "assertions": []
}
```

### 第 2 步：在运行进行时起草断言

不要只是等待运行结束 —— 你可以 productive 地使用这段时间。为每个测试用例起草定量断言并向用户解释它们。如果 `evals/evals.json` 中已经存在断言，审查它们并解释它们检查了什么。

好的断言是可客观验证的并且有描述性名称 —— 它们在基准查看器中应读起来清晰，以至于某人在瞥见结果时立即理解每个断言检查的是什么。主观技能（写作风格、设计质量）更适合定性评估 —— 不要强迫断言到需要人类判断的事情上。

一旦起草完毕，更新 `eval_metadata.json` 文件和 `evals/evals.json`。也向用户解释他们将在查看器中看到什么 —— 定性输出和定量基准。

### 第 3 步：运行完成后，捕获时间数据

当每个子代理任务完成时，你会收到一个包含 `total_tokens` 和 `duration_ms` 的通知。立即将此数据保存到运行目录中的 `timing.json`：

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

这是捕获此数据的唯一机会 —— 它通过任务通知到达，不会持久保存在其他地方。在处理每个通知时进行处理，而不是试图批处理它们。

### 第 4 步：评分、聚合和启动查看器

在所有运行完成后：

1. **为每个运行评分** —— 派生一个分级子代理（或内联评分）阅读 `agents/grader.md` 并针对每个输出来评估每个断言。将结果保存到每个运行目录中的 `grading.json`。grading.json 期望数组必须使用 `text`、`passed` 和 `evidence` 字段（不是 `name`/`met`/`details` 或其他变体）—— 查看器依赖于这些确切的字段名。对于可以编程检查的断言，编写并运行脚本而不是用肉眼检查 —— 脚本更快、更可靠，并且可以在跨迭代之间重用。

2. **聚合成基准** —— 从技能创建器目录运行聚合脚本：
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   这将产生 `benchmark.json` 和 `benchmark.md`，其中包含每个配置的 pass_rate、时间和令牌，带有均值 ± 标准差和差值。如果手动生成 benchmark.json，参见 `references/schemas.md` 获取查看器所需的精确模式。
   将每个 with_skill 版本放在其基线对应项之前。

3. **进行分析师审查** —— 读取基准数据并揭示聚合统计数据可能隐藏的模式。参见 `agents/analyzer.md`（"分析基准结果"部分）以了解要寻找什么 —— 比如不管技能如何总是通过的断言（非判别性）、高方差的 evals（可能是易错的），以及时间和令牌的权衡。

4. **使用定性和定量数据启动查看器：**
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   对于 iteration 2+，也传递 `--previous-workspace <workspace>/iteration-<N-1>`。

   **Cowork / headless 环境:** 如果 `webbrowser.open()` 不可用或环境没有显示器，使用 `--static <output_path>` 写入一个独立 HTML 文件而不是启动服务器。当用户点击"提交所有评论"时，反馈将以 `feedback.json` 文件下载。下载后，将 `feedback.json` 复制到工作区目录以供下一次迭代拾取。

注意：请使用 generate_review.py 创建查看器；不需要编写自定义 HTML。

5. **告诉用户** 类似这样的内容："我已在浏览器中打开了结果。有两个选项卡 —— 'Outputs' 允许你逐一切过每个测试用例并留下反馈，'Benchmark' 显示定量比较。完成后，回到这里告诉我。"

### 用户在查看器中看到的内容

"Outputs" 选项卡一次显示一个测试用例：
- **提示词**: 给出的任务
- **输出**: 技能生成的文件，尽可能内联渲染
- **之前的输出**（iteration 2+）：折叠部分显示上一次迭代的输出
- **正式评分**（如果运行了评分）：折叠部分显示断言通过/失败
- **反馈**：一个文本框，在用户输入时自动保存
- **之前的反馈**（iteration 2+）：上次他们从那时起的评论，显示在文本框下方

"Benchmark" 选项卡显示统计摘要：每个配置的通过率、时间和令牌使用量，带有每个 eval 分解和分析师观察。

导航通过 prev/next 按钮或箭头键进行。完成后，他们点击"提交所有评论"，它将所有反馈保存到 `feedback.json`。

### 第 5 步：读取反馈

当用户告诉你他们完成了，读取 `feedback.json`：

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "图表缺少轴标签", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "完美，喜欢这个", "timestamp": "..."}
  ],
  "status": "complete"
}
```

空的反馈意味着用户认为它没问题。专注于用户对之有特定投诉的测试用例以进行改进。

当你完成它时，杀死查看器服务器：

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## 改进技能

这是循环的心脏。你已经运行了测试用例，用户已经回顾了结果，现在你需要根据他们的反馈让技能变得更好。

### 如何思考改进

1. **从反馈中泛化。** 这里发生的事情的大图是我们正在尝试创建可以被使用一百万次（也许是字面意思，也许更多谁知道）的技能 across many different prompts。在这里，你和用户一遍又一遍地在只有几个示例上迭代，因为这有助于移动得更快。用户深入了解了这些示例，他们可以很快评估新的输出。但如果你和用户共同开发的技能仅适用于那些示例，它就是无用的。与其放入杂乱的过度调整的变化，或压迫性限制性 MUSTS，如果有一个顽固的问题，你可能会尝试分支出去并使用不同的隐喻，或推荐不同的工作模式。尝试相对便宜，也许你会 landing 在一些伟大的东西上。

2. **保持提示简洁。** 移除不在其重量的东西。确保读取转录，而不仅仅是最终输出 —— 如果看起来技能是让模型浪费大量时间做不生产的事情，你可以尝试去除使其那样的部分的技能，看看会发生什么。

3. **解释为什么。** 尽力解释你所要求的模型背后的 **为什么**。今天的 LLMs 是*聪明的*。他们有良好的心智理论和当给予一个好的 harness 可以超越死板的指令真正使事情发生。即使来自用户的反馈是简短的或沮丧的，试着实际理解任务和为什么用户写他们写的，和他们实际写的，然后传输这个理解到指令中。如果你在所有的 caps 中写 ALWAYS 或 NEVER，或使用超级 rigid 的结构，那是一个黄色标志 —— 如果可能，重新框架并解释原因，以便模型理解为什么你要求的事情很重要。这是一种更人性化、更有力量和有效的方法。

4. **查看 across test cases 中的重复工作。** 从测试运行中读取转录并注意如果所有子代理都独立地写了类似的帮助脚本或采取了相同的多步骤方法来做某事。如果所有 3 个测试用例 resulted in the subagent writing a `create_docx.py` or a `build_chart.py`, that's a strong signal the skill should bundle that script. Write it once, put it in `scripts/`, and tell the skill to use it. This saves every future invocation from reinventing the wheel.

This task is pretty important (we are trying to create billions a year in economic value here!) and your thinking time is not the blocker; take your time and really mull things over. I'd suggest writing a draft revision and then looking at it anew and making improvements. Really do your best to get into the the user and understand what they want and need.

### 迭代循环

After improving the skill:

1. Apply your improvements to the skill
2. Rerun all test cases into a new `iteration-<N+1>/` directory, including baseline runs. If you're creating a new skill, the baseline is always `without_skill` (no skill) — that stays the same across iterations. If you're improving an existing skill, use your judgment on what makes sense as the baseline: the original version the user came in with, or the previous iteration.
3. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review and tell you they're done
5. Read the new feedback, improve again, repeat

Keep going until:
- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress

---

## Advanced: Blind comparison

For situations where you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?"), there's a blind comparison系统。Read `agents/comparator.md` and `agents/analyzer.md` for the details. The basic idea is: give two outputs to an independent agent without telling it which is which, and let it judge quality. Then analyze why the winner won.

This is optional, requires subagents, and most users won't need it. The human review loop is usually sufficient.

---

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### Step 1: Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

The queries must be realistic and something a Claude Code or Claude.ai user would actually type. Not abstract requests, but requests that are concrete and specific and have a good amount of detail. For instance, file paths, personal context about the user's job or situation, column names and values, company names, URLs. A little bit of backstory. Some might be in lowercase or contain abbreviations or typos or casual speech. Use a mix of different lengths, and focus on edge cases rather than making them clear-cut (the user will get a chance to sign off on them).

Bad: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

Good: `"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

For the **should-trigger** queries (8-10), think about coverage. You want different phrasings of the same intent — some formal, some casual. Include cases where the user doesn't explicitly name the skill or file type but clearly needs it. Throw in some uncommon use cases and cases where this skill competes with another but should win.

For the **should-not-trigger** queries (8-10), the most valuable ones are the near-misses — queries that share keywords or concepts with the skill but actually need something different. Think adjacent domains, ambiguous phrasing where a naive keyword match would trigger but shouldn't, and cases where the query touches on something the skill does but in a context where another tool is more appropriate.

The key thing to avoid: don't make should-not-trigger queries obviously irrelevant. "Write a fibonacci function" as a negative test for a PDF skill is too easy — it doesn't test anything. The negative cases should be genuinely tricky.

### Step 2: Review with user

Present the eval set to the user for review using the HTML template:

1. Read the template from `assets/eval_review.html`
2. Replace the placeholders:
   - `__EVAL_DATA_PLACEHOLDER__` → the JSON array of eval items (no quotes around it — it's a JS variable assignment)
   - `__SKILL_NAME_PLACEHOLDER__` → the skill's name
   - `__SKILL_DESCRIPTION_PLACEHOLDER__` → the skill's current description
3. Write to a temp file (e.g., `/tmp/eval_review_<skill-name>.html`) and open it: `open /tmp/eval_review_<skill-name>.html`
4. The user can edit queries, toggle should-trigger, add/remove entries, then click "Export Eval Set"
5. The file downloads to `~/Downloads/eval_set.json` — check the Downloads folder for the most recent version in case there are multiple (e.g., `eval_set (1).json`)

This step matters — bad eval queries lead to bad descriptions.

### Step 3: Run the optimization loop

Tell the user: "This will take some time — I'll run the optimization loop in the background and check on it periodically."

Save the eval set to the workspace, then run in the background:

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the model ID from your system prompt (the one powering the current session) so the triggering test matches what the user actually experiences.

While it runs, periodically tail the output to give the user updates on which iteration it's on and what the scores look like.

This handles the full optimization loop automatically. It splits the eval set into 60% train and 40% held-out test, evaluates the current description (running each query 3 times to get a reliable trigger rate), then calls Claude to propose improvements based on what failed. It re-evaluates each new description on both train and test, iterating up to 5 times. When it's done, it opens an HTML report in the browser showing the results per iteration and returns JSON with `best_description` — selected by test score rather than train score to avoid overfitting.

### How skill triggering works

Understanding the triggering mechanism helps design better eval queries. Skills appear in Claude's `available_skills` list with their name + description, and Claude decides whether to consult a skill based on that description. The important thing to know is that Claude only consults skills for tasks it can't easily handle on its own — simple, one-step queries like "read this PDF" may not trigger a skill even if the description matches perfectly, because Claude can handle them directly with basic tools. Complex, multi-step, or specialized queries reliably trigger skills when the description matches.

This means your eval queries should be substantive enough that Claude would actually benefit from consulting a skill. Simple queries like "read file X" are poor test cases — they won't trigger skills regardless of description quality.

### Step 4: Apply the result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter. Show the user before/after and report the scores.

---

### Package and Present (only if `present_files` tool is available)

Check whether you have access to the `present_files` tool. If you don't, skip this step. If you do, package the skill and present the .skill file to the user:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

After packaging, direct the user to the resulting `.skill` file path so they can install it.

---

## Claude.ai-specific instructions

In Claude.ai, the core workflow is the same (draft → test → review → improve → repeat), but because Claude.ai doesn't have subagents, some mechanics change. Here's what to adapt:

**Running test cases**: No subagents means no parallel execution. For each test case, read the skill's SKILL.md, then follow its instructions to accomplish the test prompt yourself. Do them one at a time. This is less rigorous than independent subagents (you wrote the skill and you're also running it, so you have full context), but it's a useful sanity check — and the human review step compensates. Skip the baseline runs — just use the skill to complete the task as requested.

**Reviewing results**: If you can't open a browser (e.g., Claude.ai's VM has no display, or you're on a remote server), skip the browser reviewer entirely. Instead, present results directly in the conversation. For each test case, show the prompt and the output. If the output is a file the user needs to see (like a .docx or .xlsx), save it to the filesystem and tell them where it is so they can download and inspect it. Ask for feedback inline: "How does this look? Anything you'd change?"

**Benchmarking**: Skip the quantitative benchmarking — it relies on baseline comparisons which aren't meaningful without subagents. Focus on qualitative feedback from the user.

**The iteration loop**: Same as before — improve the skill, rerun the test cases, ask for feedback — just without the browser reviewer in the middle. You can still organize results into iteration directories on the filesystem if you have one.

**Description optimization**: This section requires the `claude` CLI tool (specifically `claude -p`) which is only available in Claude Code. Skip it if you're on Claude.ai.

**Blind comparison**: Requires subagents. Skip it.

**Packaging**: The `package_skill.py` script works anywhere with Python and a filesystem. On Claude.ai, you can run it and the user can download the resulting `.skill` file.

**Updating an existing skill**: The user might be asking you to update an existing skill, not create a new one. In this case:
- **Preserve the original name.** Note the skill's directory name and `name` frontmatter field -- use them unchanged. E.g., if the installed skill is `research-helper`, output `research-helper.skill` (not `research-helper-v2`).
- **Copy to a writeable location before editing.** The installed skill path may be read-only. Copy to `/tmp/skill-name/`, edit there, and package from the copy.
- **If packaging manually, stage in `/tmp/` first**, then copy to the output directory -- direct writes may fail due to permissions.

---

## Cowork-Specific Instructions

If you're in Cowork, the main things to know are:

- You have subagents, so the main workflow (spawn test cases in parallel, run baselines, grade, etc.) all works. (However, if you run into severe problems with timeouts, it's OK to run the test prompts in series rather than parallel.)
- You don't have a browser or display, so when generating the eval viewer, use `--static <output_path>` to write a standalone HTML file instead of starting a server. Then proffer a link that the user can click to open the HTML in their browser.
- For whatever reason, the Cowork setup seems to disincline Claude from generating the eval viewer after running the tests, so just to reiterate: whether you're in Cowork or in Claude Code, after running tests, you should always generate the eval viewer for the human to look at examples before revising the skill yourself and trying to make corrections, using `generate_review.py` (not writing your own boutique html code). Sorry in advance but I'm gonna go all caps here: GENERATE THE EVAL VIEWER *BEFORE* evaluating inputs yourself. You want to get them in front of the human ASAP!
- Feedback works differently: since there's no running server, the viewer's "Submit All Reviews" button will download `feedback.json` as a file. You can then read it from there (you may have to request access first).
- Packaging works — `package_skill.py` just needs Python and a filesystem.
- Description optimization (`run_loop.py` / `run_eval.py`) should work in Cowork just fine since it uses `claude -p` via subprocess, not a browser, but please save it until you've fully finished making the skill and the user agrees it's in good shape.
- **Updating an existing skill**: The user might be asking you to update an existing skill, not create a new one. Follow the update guidance in the claude.ai section above.

---

## Reference files

The agents/ directory contains instructions for specialized subagents. Read them when you need to spawn the relevant subagent.

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison between two outputs
- `agents/analyzer.md` — How to analyze why one version beat another

The references/ directory has additional documentation:
- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.

---

Repeating one more time the core loop here for emphasis:

- Figure out what the skill is about
- Draft or edit the skill
- Run claude-with-access-to-the-skill on test prompts
- With the user, evaluate the outputs:
  - Create benchmark.json and run `eval-viewer/generate_review.py` to help the user review them
  - Run quantitative evals
- Repeat until you and the user are satisfied
- Package the final skill and return it to the user.

Please add steps to your TodoList, if you have such a thing, to make sure you don't forget. If you're in Cowork, please specifically put "Create evals JSON and run `eval-viewer/generate_review.py` so human can review test cases" in your TodoList to make sure it happens.

Good luck!
