"""Export reproducible stage records and plain-language experiment summaries."""
import csv
import io
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .common import digest, redact, write_json


def now():
    return datetime.now(timezone.utc).isoformat()


def event(directory, state, name, **details):
    record = {'timestamp_utc': now(), 'event': name, **details}
    with (Path(directory) / 'events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(redact(json.dumps(record, ensure_ascii=False)) + '\n')
    state['last_event'] = record


def configuration(root, paths, cases, **options):
    packages = {}
    for package in ['pytest', 'pytest-playwright', 'playwright', 'requests', 'openai']:
        try:
            packages[package] = version(package)
        except PackageNotFoundError:
            packages[package] = 'unavailable'
    return {'created_at_utc': now(), 'python': sys.version, 'executable': sys.executable,
            'platform': platform.platform(), 'packages': packages, 'options': options,
            'case_data_sha256': digest(Path(root) / 'generated_test_cases.json'),
            'selected': [{'test_id': p.stem.removeprefix('test_').upper(),
                          'source_sha256': digest(p)} for p in paths],
            'case_data': cases}


def export(directory, state):
    directory = Path(directory)
    initial = state.get('initial', state.get('baseline', []))
    attempts = state.get('attempts', [])
    regression = {r['test_id']: r for r in state.get('regression', [])}
    initial_map = {r['test_id']: r for r in initial}
    types = state.get('case_types', {})
    all_ids = sorted(set(initial_map) | set(regression))
    rows, stage_rows = [], []
    for test_id in all_ids:
        before = initial_map.get(test_id, {})
        history = [a for a in attempts if a['test_id'] == test_id]
        applied = [a for a in history if a.get('decision') == 'applied']
        retests = [a['result'] for a in history if a.get('result')]
        latest_retest = retests[-1] if retests else {}
        final = regression.get(test_id) or latest_retest or before
        rows.append({'test_id': test_id, 'test_type': types.get(test_id, ''),
                     'initial_status': before.get('status', 'not_run'),
                     'initial_classification': before.get('classification', ''),
                     'initial_seconds': before.get('duration', ''),
                     'ai_analyses': len(history),
                     'proposals': sum(bool(a['analysis'].get('repaired_code')) for a in history),
                     'applied_rounds': len(applied),
                     'latest_ai_category': history[-1]['analysis']['category'] if history else '',
                     'last_decision': history[-1]['decision'] if history else '',
                     'last_reason': history[-1].get('reason', '') if history else '',
                     'retest_status': latest_retest.get('status', 'not_run'),
                     'regression_status': regression.get(test_id, {}).get('status', 'not_run'),
                     'final_observed_status': final.get('status', 'not_run'),
                     'final_classification': final.get('classification', ''),
                     'initial_evidence': before.get('directory', ''),
                     'final_evidence': final.get('directory', '')})
    for stage in ['baseline', 'initial', 'regression']:
        for result in state.get(stage, []):
            stage_rows.append(_stage_row(stage, 0, result))
    for a in attempts:
        if a.get('result'):
            stage_rows.append(_stage_row('retest', a['round'], a['result']))
    for filename, values in [('cases.csv', rows), ('stage_results.csv', stage_rows)]:
        output = io.StringIO(newline='')
        if values:
            writer = csv.DictWriter(output, fieldnames=list(values[0]))
            writer.writeheader()
            writer.writerows(values)
        (directory / filename).write_text(redact(output.getvalue()), encoding='utf-8-sig', newline='')
    applied_ids = {r['test_id'] for r in rows if r['applied_rounds']}
    metrics = {'initial': _counts(initial), 'regression': _counts(list(regression.values())),
               'analyses': len(attempts), 'analyzed_cases': len({a['test_id'] for a in attempts}),
               'proposals': sum(r['proposals'] for r in rows), 'modified_cases': len(applied_ids),
               'applied_rounds': sum(r['applied_rounds'] for r in rows),
               'modified_retest_passed': sum(r['retest_status'] == 'passed' for r in rows if r['test_id'] in applied_ids),
               'modified_retest_failed': sum(r['retest_status'] == 'failed' for r in rows if r['test_id'] in applied_ids),
               'modified_final_passed': sum(r['final_observed_status'] == 'passed' for r in rows if r['test_id'] in applied_ids),
               'modified_final_failed': sum(r['final_observed_status'] == 'failed' for r in rows if r['test_id'] in applied_ids),
               'human_review_cases': sum(r['last_decision'] == 'human_review' for r in rows),
               'initial_failures_now_passed': [r['test_id'] for r in rows if r['initial_status'] == 'failed' and r['final_observed_status'] == 'passed'],
               'initial_passes_now_failed': [r['test_id'] for r in rows if r['initial_status'] == 'passed' and r['final_observed_status'] == 'failed'],
               'final_observed': _counts_from_rows(rows),
               'ai_seconds': round(sum(a.get('analysis_seconds', 0) for a in attempts), 3)}
    # Token usage may include nested detail dictionaries; aggregate scalar totals only.
    metrics['tokens'] = {name: sum((a['analysis'].get('usage') or {}).get(name, 0) or 0 for a in attempts)
                         for name in ['prompt_tokens', 'completion_tokens', 'total_tokens']}
    write_json(directory / 'metrics.json', metrics)
    state['metrics'] = metrics
    timestamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S 北京时间')
    m = metrics
    status = '完成' if state.get('finished') else ('已中断' if state.get('interrupted') or state.get('ended_at_utc') else '进行中')
    lines = ['# 本次自动修复实验汇总', '', f"运行编号：`{state['run_id']}`", '',
             f"更新时间：{timestamp}；流程状态：{status}。", '',
             '执行失败数不等于脚本缺陷数；环境、测试数据、收集及准备错误需单独分析。', '',
             '以下数字仅属于本次真实执行；不混入历史运行或本地模拟验证。', '',
             '| 阶段 | 总数 | 通过 | 失败 | 跳过 |', '| --- | ---: | ---: | ---: | ---: |']
    for label, key in [('raw 首次运行', 'initial'), ('修改后的全量回归', 'regression'), ('当前最新已观察结果', 'final_observed')]:
        c = m[key]
        lines.append(f"| {label} | {c['total']} | {c['passed']} | {c['failed']} | {c['skipped']} |")
    if not state.get('finished'):
        planned = state.get('regression_planned_count', len(types))
        lines += ['', f"流程尚未完成；回归仅记录 {len(regression)}/{planned} 条，不代表完整修复后结果。"]
    if state.get('interruption_reason'):
        lines += ['', '中断原因：' + state['interruption_reason']]
    lines += ['', '首次执行分类（保留该次执行器的原始判断；不代表已确认的根因）：', '',
              '| 分类 | 数量 |', '| --- | ---: |']
    for category, count in m['initial']['classifications'].items():
        lines.append(f'| {category} | {count} |')
    lines += ['', '## 实际修复了多少', '',
              f"- AI 分析了 {m['analyzed_cases']} 条用例，共 {m['analyses']} 次，耗时 {m['ai_seconds']} 秒。",
              f"- AI 输出了 {m['proposals']} 份含代码的提案；实际修改 {m['modified_cases']} 条用例，共应用 {m['applied_rounds']} 轮修改。",
              f"- 实际修改的用例中，最近一次修复重跑：通过 {m['modified_retest_passed']} 条、失败 {m['modified_retest_failed']} 条。",
              f"- 实际修改的用例在最新结果中：通过 {m['modified_final_passed']} 条、失败 {m['modified_final_failed']} 条。",
              f"- {m['human_review_cases']} 条用例需要人工核查（包括环境或数据问题、未提供修复代码及被拒绝的提案）。", '',
              '未发生修改的用例不算作自动修复成功；网络恢复导致的通过也不能单独归因于代码修复。', '',
              '## 按用例查看', '',
              '| 用例 | 类型 | 首次结果 | AI 分类 | 应用修改轮数 | 修复重跑 | 全量回归 | 最新结果 |',
              '| --- | --- | --- | --- | ---: | --- | --- | --- |']
    translate = {'passed': '通过', 'failed': '失败', 'skipped': '跳过', 'not_run': '未运行'}
    for r in rows:
        lines.append(f"| {r['test_id']} | {r['test_type']} | {translate[r['initial_status']]} | {r['latest_ai_category']} | {r['applied_rounds']} | {translate[r['retest_status']]} | {translate[r['regression_status']]} | {translate[r['final_observed_status']]} |")
    lines += ['', '## 证据位置', '',
              '- `configuration.json`、`inputs/`：运行环境、配置、全部初始源码、用例及框架版本快照。',
              '- `events.jsonl`：按时间追加的阶段开始、结束及每条测试事件。',
              '- `initial/`：每条 raw 首次执行的结果、日志、源代码、失败截图、DOM 和浏览器追踪。',
              '- `repairs/<用例>/<轮次>/`：AI 请求和响应、分析、修复决定、原代码、候选代码、差异及重跑记录。',
              '- `regression/`：发生代码修改后，全量回归的逐条记录。',
              '- `cases.csv`：一条用例一行，适合汇总；`stage_results.csv`：每次执行一行，适合分析各轮耗时和变化。',
              '- `metrics.json`：程序计算的统计；`run.json`：完整关联数据。', '',
              '未运行阶段标记为“未运行”，不会把首次执行结果冒充修复后回归结果。', '',
              f"手工版本和固定基线核对：{state.get('protected_files_unchanged', '流程结束后核对')}。"]
    (directory / 'summary_zh.md').write_text(redact('\n'.join(lines)), encoding='utf-8')


def _counts(results):
    c = Counter(r['status'] for r in results)
    return {'total': len(results), 'passed': c['passed'], 'failed': c['failed'], 'skipped': c['skipped'],
            'classifications': dict(Counter(r['classification'] for r in results))}


def _counts_from_rows(rows):
    c = Counter(r['final_observed_status'] for r in rows)
    return {'total': len(rows), 'passed': c['passed'], 'failed': c['failed'], 'skipped': c['skipped']}


def _stage_row(stage, round_number, result):
    return {'stage': stage, 'round': round_number, 'test_id': result['test_id'],
            'status': result['status'], 'phase': result['phase'], 'classification': result['classification'],
            'duration_seconds': result['duration'], 'source_sha256': result.get('source_sha256', ''),
            'evidence_directory': result['directory']}
