# AI-assisted test generation and repair

This repository contains test generation, execution and AI repair code, together with the initially generated tests, manual revisions and final comparison cases. Existing tests were collected from saved versions without generating new tests or execution results.

## Repository contents

| File or directory | Description |
| --- | --- |
| `generate_case.py` | Generates structured test cases from requirements |
| `script_gen.py` | Generates test scripts and contains their generation prompts |
| `ai_run_and_repair.py` | Runs raw tests and requests AI analysis and repair; contains `AI_REPAIR_SYSTEM_PROMPT` |
| `run_failed_ai_repair.py` | Historical tool for analyzing and applying guarded repairs to failed cases |
| `run_aggressive_ai_repair.py` | Later repair tool; contains the `SYSTEM` repair prompt and supports case selection with `--ids` |
| `testflow/` | Execution, AI calls, repair validation and report generation |
| `tests/test_workflow.py` | Framework validation tests |
| `generated_test_cases.json` | Generated structured test cases |
| `baselines/raw_initial/` | Fixed snapshots of the 42 initially generated raw scripts |
| `manual_tests/` | The 42 manual versions previously stored directly under `generated_tests/` |
| `generated_tests/case_raw/` | Working copies used for later execution and repair; some differ from the initial versions |
| `generated_tests/case_ai_final/` | Existing final versions of 17 selected comparison cases; see its README for sources |
| `baselines/preservation.json` | File protection hashes for the initial snapshots and manual versions |

The removal of `generated_tests/test_tc_*.py` and addition of `manual_tests/` represent a file migration.

## The 17 comparison cases

```text
TC_001 TC_005 TC_006 TC_007 TC_010 TC_012 TC_013 TC_014 TC_015
TC_017 TC_018 TC_019 TC_022 TC_023 TC_025 TC_026 TC_028
```

Saved AI repair candidate source exists for 15 cases. TC_007 comes from an existing manual patch archive, and TC_028 retains its unmodified AI-generated version. This set is therefore described as final comparison code rather than 17 AI repairs. `case_ai_final/sources.json` records each file's source and SHA-256.

These files support source comparisons and do not establish a successful full regression. Some working scripts and the aggressive repair prompt replace the site's JavaScript with empty responses and change navigation waiting strategies, affecting page behavior. Static checks in the aggressive repair tool differ from the main workflow's AST protection.

## Setup and entry points

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
Copy-Item .env.example .env
```

Set `DEEPSEEK_API_KEY` in your local `.env`. Actual credentials are excluded from the repository.

```powershell
# Show the prompt without executing tests
.\.venv\Scripts\python.exe ai_run_and_repair.py --show-prompt

# Execute working copies without calling AI
.\.venv\Scripts\python.exe -m testflow run --no-ai

# Execute the fixed initial versions without modifying the baseline
.\.venv\Scripts\python.exe -m testflow run --baseline --no-ai

# Run AI analysis and guarded repair, modifying working copies and running regression
.\.venv\Scripts\python.exe ai_run_and_repair.py --ids TC_007

# Validate the framework
.\.venv\Scripts\python.exe -m pytest -q
```

The AI entry point executes code through local pytest, then sends failed source and textual evidence to the model. `run_failed_ai_repair.py` and `run_aggressive_ai_repair.py` preserve historical repair logic. Their default inputs require existing local `runs/` records that are excluded from this source delivery. Their prompts and logic can be read directly; specifying `--ids` does not supply missing historical inputs.

Regular pytest collects only `tests/`. Logs, screenshots, traces, historical execution directories, report build files and local dependencies are excluded from this source delivery. No live website tests or AI calls were performed to collect these files.
