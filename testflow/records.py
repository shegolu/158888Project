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
    timestamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S UTC+08:00')
    m = metrics
    status = 'Completed' if state.get('finished') else ('Interrupted' if state.get('interrupted') or state.get('ended_at_utc') else 'In progress')
    lines = ['# Automated repair experiment summary', '', f"Run ID: `{state['run_id']}`", '',
             f"Updated: {timestamp}; workflow status: {status}.", '',
             'Execution failures do not equal script defects; environment, test data, collection and setup errors require separate analysis.', '',
             'These figures describe this execution only; historical runs and local simulated validation are excluded.', '',
             '| Stage | Total | Passed | Failed | Skipped |', '| --- | ---: | ---: | ---: | ---: |']
    for label, key in [('Initial raw execution', 'initial'), ('Full regression after changes', 'regression'), ('Latest observed results', 'final_observed')]:
        c = m[key]
        lines.append(f"| {label} | {c['total']} | {c['passed']} | {c['failed']} | {c['skipped']} |")
    if not state.get('finished'):
        planned = state.get('regression_planned_count', len(types))
        lines += ['', f"The workflow is incomplete; regression records cover only {len(regression)}/{planned} cases and do not represent complete post-repair results."]
    if state.get('interruption_reason'):
        lines += ['', 'Interruption reason: ' + state['interruption_reason']]
    lines += ['', 'Initial execution classifications (original executor judgments, not confirmed root causes):', '',
              '| Classification | Count |', '| --- | ---: |']
    for category, count in m['initial']['classifications'].items():
        lines.append(f'| {category} | {count} |')
    lines += ['', '## Applied repairs', '',
              f"- AI analyzed {m['analyzed_cases']} cases in {m['analyses']} analyses, taking {m['ai_seconds']} seconds.",
              f"- AI produced {m['proposals']} code proposals; {m['modified_cases']} cases were modified in {m['applied_rounds']} applied repair rounds.",
              f"- Latest repair reruns for modified cases: {m['modified_retest_passed']} passed and {m['modified_retest_failed']} failed.",
              f"- Latest observed results for modified cases: {m['modified_final_passed']} passed and {m['modified_final_failed']} failed.",
              f"- {m['human_review_cases']} cases require human review, including environment or data issues, missing repair code and rejected proposals.", '',
              'Unmodified cases do not count as successful automatic repairs; a pass after network recovery cannot be attributed to a code repair alone.', '',
              '## Results by case', '',
              '| Case | Type | Initial result | AI category | Applied rounds | Repair rerun | Full regression | Latest result |',
              '| --- | --- | --- | --- | ---: | --- | --- | --- |']
    translate = {'passed': 'Passed', 'failed': 'Failed', 'skipped': 'Skipped', 'not_run': 'Not run'}
    for r in rows:
        lines.append(f"| {r['test_id']} | {r['test_type']} | {translate[r['initial_status']]} | {r['latest_ai_category']} | {r['applied_rounds']} | {translate[r['retest_status']]} | {translate[r['regression_status']]} | {translate[r['final_observed_status']]} |")
    lines += ['', '## Evidence locations', '',
              '- `configuration.json`, `inputs/`: environment, configuration, initial sources, cases and framework snapshots.',
              '- `events.jsonl`: chronological stage start, stage end and individual test events.',
              '- `initial/`: initial raw execution results, logs, source, failure screenshots, DOM and browser traces.',
              '- `repairs/<case>/<round>/`: AI requests and responses, analysis, repair decisions, original and candidate code, diffs and rerun records.',
              '- `regression/`: individual full regression records after code changes.',
              '- `cases.csv`: one row per case for summaries; `stage_results.csv`: one row per execution for timing and change analysis.',
              '- `metrics.json`: computed statistics; `run.json`: complete linked data.', '',
              'Unexecuted stages are marked "Not run"; initial results are not presented as post-repair regression results.', '',
              f"Manual version and fixed baseline integrity: {state.get('protected_files_unchanged', 'Checked when the workflow ends')}."]
    (directory / 'summary.md').write_text(redact('\n'.join(lines)), encoding='utf-8')


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
