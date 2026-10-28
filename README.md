# AI-assisted test generation and repair

本仓库保存测试生成、执行与 AI 修复源码，以及首次生成版、人工版和最终对照用例。现有用例直接从保存的版本整理，没有重新生成，也没有新增运行结果。

## 代码位置

| 文件或目录 | 内容 |
| --- | --- |
| `generate_case.py` | 根据需求生成结构化用例 |
| `script_gen.py` | 生成测试脚本及其 prompt |
| `ai_run_and_repair.py` | 执行 raw、调用 AI 分析和修复的入口；`AI_REPAIR_SYSTEM_PROMPT` 保存提示词 |
| `run_failed_ai_repair.py` | 对失败用例进行分析和受控修复的历史工具 |
| `run_aggressive_ai_repair.py` | 后续修复工具；`SYSTEM` 保存修复 prompt，支持通过 `--ids` 选择用例 |
| `testflow/` | 执行器、AI 调用、修复检查与报告实现 |
| `tests/test_workflow.py` | 框架验证代码 |
| `generated_test_cases.json` | 生成后的结构化用例 |
| `baselines/raw_initial/` | 首次生成的 42 个 raw 脚本固定副本 |
| `manual_tests/` | 原 `generated_tests/` 根目录下的 42 个手工版本 |
| `generated_tests/case_raw/` | 后续执行与修复的工作副本，部分已修改，不再等同于首次生成版 |
| `generated_tests/case_ai_final/` | 17 条选定用例的现有最终对照代码，来源见该目录说明 |
| `baselines/preservation.json` | 首次生成版和手工版的文件保护哈希 |

旧 `generated_tests/test_tc_*.py` 的删除与 `manual_tests/` 的新增属于文件迁移。

## 17 条对照用例

```text
TC_001 TC_005 TC_006 TC_007 TC_010 TC_012 TC_013 TC_014 TC_015
TC_017 TC_018 TC_019 TC_022 TC_023 TC_025 TC_026 TC_028
```

其中 15 条有保存的 AI 修复候选源码；TC_007 来自现有人工补丁存档；TC_028 保留未修改的 AI 原始版本。因此这组文件称为最终对照代码，不统一声称是 17 条 AI 修复成果。`case_ai_final/sources.json` 记录各文件的来源和 SHA-256。

这些文件供源码比较，不代表一次完整回归的通过结果。部分工作脚本和激进修复提示词会把网站自身 JavaScript 替换为空响应，并更改导航等待策略；该条件会影响被测页面行为。激进修复工具的静态检查不同于主流程的 AST 保护。

## 环境与入口

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
```

在本机 `.env` 中填写 `DEEPSEEK_API_KEY`。真实密钥不纳入仓库。

```powershell
# 查看提示词，不运行用例
.\.venv\Scripts\python.exe ai_run_and_repair.py --show-prompt

# 仅执行工作副本，不调用 AI
.\.venv\Scripts\python.exe -m testflow run --no-ai

# 执行固定的首次生成版，不修改基线
.\.venv\Scripts\python.exe -m testflow run --baseline --no-ai

# 显式执行 AI 分析和受控修复，会修改工作副本并进行回归
.\.venv\Scripts\python.exe ai_run_and_repair.py --ids TC_007

# 验证框架本身
.\.venv\Scripts\python.exe -m pytest -q
```

AI 入口通过本地 pytest 执行代码，再把失败源码和文本证据传给模型。`run_failed_ai_repair.py` 和 `run_aggressive_ai_repair.py` 保留历史修复逻辑，其默认输入依赖本机 `runs/` 中已有记录，未随源码交付包含。它们的 prompt 和处理逻辑可直接阅读；指定 `--ids` 不会自动补齐历史输入。

普通 pytest 只收集 `tests/`。日志、截图、trace、历史执行目录、报告构建文件与本地依赖不属于这次源码提交；没有为此次整理重新运行真实网站或调用 AI。
