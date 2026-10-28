import difflib
import json
import os
import shutil
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .ai import DeepSeek, validate_analysis
from .common import ROOT, digest, raw_target, redact, write_json
from .guard import Rejected, validate
from .layout import hashes, prepare
from .runner import execute, select
from .records import configuration, event, export, now


def analyze(result, case, analyzer, directory=None):
    try:
        context = dict(result)
        if directory is not None:
            context['_analysis_directory'] = str(directory)
        analysis = analyzer.analyze(context, case)
        validate_analysis(analysis)
        return analysis
    except Exception as exc:
        return {'category': 'unknown', 'summary': 'AI analysis unavailable or invalid',
                'evidence': [], 'suggestion': redact(exc), 'confidence': 0,
                'safe_to_repair': False, 'repaired_code': None, 'provider': 'unavailable'}


def apply_repair(root, result, analysis, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = raw_target(root, Path(result['script']).name)
    if digest(target) != result['source_sha256']:
        raise Rejected('Source changed since execution; refusing stale repair')
    if result['classification'] == 'environment':
        raise Rejected('Environment failures are not automatically repaired')
    if (analysis.get('category') not in {'locator', 'precondition', 'collection'}
            or not analysis.get('safe_to_repair') or analysis.get('confidence', 0) < 0.85
            or not analysis.get('evidence')):
        raise Rejected('AI evidence/category/confidence requires human review')
    code = analysis.get('repaired_code')
    if not code:
        raise Rejected('No repair code supplied')
    original = target.read_text(encoding='utf-8')
    if original == code:
        raise Rejected('Candidate contains no change')
    # Save every proposal before checking it; rejected code is never executed.
    (directory / 'before.py').write_bytes(target.read_bytes())
    (directory / 'candidate.py').write_text(code, encoding='utf-8')
    (directory / 'change.diff').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), code.splitlines(True), fromfile=target.name,
        tofile=target.name + '.candidate')), encoding='utf-8')
    validate(original, code)
    # Only this allowlisted, existing raw file is ever written by the repair path.
    with target.open('w', encoding='utf-8', newline='') as stream:
        stream.write(code)
    return {'target': str(target), 'before_sha256': result['source_sha256'],
            'after_sha256': digest(target), 'diff': str(directory / 'change.diff')}


def summary(results):
    counts = Counter(r['status'] for r in results)
    return {'total': len(results), 'passed': counts['passed'], 'failed': counts['failed'],
            'skipped': counts['skipped'],
            'pass_rate': round(counts['passed'] / len(results), 4) if results else 0,
            'duration': round(sum(r['duration'] for r in results), 3),
            'classifications': dict(Counter(r['classification'] for r in results))}


def report(run_dir, state):
    export(run_dir, state)
    write_json(Path(run_dir) / 'run.json', state)
    lines = ['# Test execution and AI repair report', '', f"Run: `{state['run_id']}`", '',
             'Initial results describe the current working copy at this run, not the first-ever AI generation.',
             'Fixed snapshot: `baselines/raw_initial/`. No historical first-pass rate is inferred.', '',
             f"Mode: {state['mode']}; baseline matches at start: {state.get('baseline_matches_at_start')}", '',
             '| Stage | Total | Passed | Failed | Skipped | Pass rate | Seconds |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for stage in ['baseline', 'initial', 'regression']:
        rows = state.get(stage, [])
        if rows:
            s = summary(rows)
            lines.append(f"| {stage} | {s['total']} | {s['passed']} | {s['failed']} | {s['skipped']} | {s['pass_rate']:.1%} | {s['duration']} |")
    lines += ['', '## Repair attempts', '']
    for attempt in state.get('attempts', []):
        a = attempt['analysis']
        lines += [f"### {attempt['test_id']} / round {attempt['round']}", '',
                  f"Decision: {attempt['decision']}", '',
                  f"Category: {a['category']}; confidence: {a['confidence']}", '',
                  a['summary'], '', 'Evidence: ' + '; '.join(a['evidence']), '',
                  'Suggestion: ' + a['suggestion'], '']
        if attempt.get('reason'):
            lines += ['Review reason: ' + attempt['reason'], '']
        if attempt.get('result'):
            r = attempt['result']
            lines += [f"Retest: {r['status']} / {r['classification']} / {r['duration']}s", '']
        if attempt.get('patch'):
            lines += [f"Diff: `{attempt['patch']['diff']}`", '']
    latest = {r['test_id']: r for r in state.get('initial', state.get('baseline', []))}
    for attempt in state.get('attempts', []):
        if attempt.get('result'):
            latest[attempt['test_id']] = attempt['result']
    for r in state.get('regression', []):
        latest[r['test_id']] = r
    lines += ['## Latest observed results', '', '| Case | Status | Phase | Classification | Evidence directory |',
              '| --- | --- | --- | --- | --- |']
    for r in latest.values():
        lines.append(f"| {r['test_id']} | {r['status']} | {r['phase']} | {r['classification']} | `{r['directory']}` |")
    lines += ['', '## Data and execution dependencies', '']
    for r in latest.values():
        for risk in r.get('data_risks', []):
            lines.append(f"- {r['test_id']}: {risk}")
    lines += ['', '## Limitations', '',
              '- Classification is diagnostic evidence, not proof of a script defect or website defect.',
              '- Static repair checks preserve assertion expressions and expected values; they do not prove business correctness.',
              '- Existing account fixtures and missing business assertions require human review. Shared accounts are not silently created/deleted.',
              '- Screenshots and traces are local evidence. Text-only DeepSeek receives DOM excerpts, not image pixels.',
              '- A timeout may prevent final browser artifacts; partial JSON and process logs remain available.']
    lines += ['', *[str(x) for x in state.get('notes', [])]]
    (Path(run_dir) / 'report.md').write_text(redact('\n'.join(lines)), encoding='utf-8')
    state['latest_summary'] = summary(list(latest.values()))
    write_json(Path(run_dir) / 'run.json', state)


def run(root=ROOT, kind='all', ids=None, no_ai=False, auto_repair=False,
        rounds=2, timeout=120, baseline=False, analyzer=None, output=None):
    root = Path(root).resolve()
    if not 1 <= rounds <= 2:
        raise ValueError('Repair rounds must be 1 or 2')
    if baseline and auto_repair:
        raise ValueError('Fixed baseline runs cannot be repaired')
    if no_ai and auto_repair:
        raise ValueError('--no-ai cannot be combined with --auto-repair')
    prepare(root)
    paths, cases = select(root, kind, ids)
    protected_before = {name: hashes(root / name) for name in ('manual_tests', 'baselines')}
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    run_dir = Path(output or root / 'runs') / run_id
    run_dir.mkdir(parents=True)
    state = {'run_id': run_id, 'mode': 'baseline' if baseline else ('auto_repair' if auto_repair else ('run_only' if no_ai else 'analyze')),
             'attempts': [], 'notes': [], 'root': str(root), 'finished': False,
             'selected_count': len(paths),
             'started_at_utc': now(), 'case_types': {k: c['test_type'] for k, c in cases.items()},
             'baseline_matches_at_start': hashes(root / 'generated_tests/case_raw') == hashes(root / 'baselines/raw_initial')}
    inputs = run_dir / 'inputs'
    inputs.mkdir()
    for path in paths:
        source = root / 'baselines/raw_initial' / path.name if baseline else path
        destination = inputs / 'raw' / path.name
        destination.parent.mkdir(exist_ok=True)
        shutil.copy2(source, destination)
    shutil.copy2(root / 'generated_test_cases.json', inputs / 'test_cases.json')
    shutil.copytree(ROOT / 'testflow', inputs / 'framework', ignore=shutil.ignore_patterns('__pycache__'))
    configured_paths = [root / 'baselines/raw_initial' / p.name for p in paths] if baseline else paths
    write_json(run_dir / 'configuration.json', configuration(root, configured_paths, cases,
               kind=kind, ids=ids, no_ai=no_ai, auto_repair=auto_repair, max_rounds=rounds,
               per_script_timeout=timeout, baseline=baseline,
               block_ad_hosts=os.getenv('TESTFLOW_BLOCK_ADS') == '1',
               navigation_timeout_ms=int(os.getenv('TESTFLOW_NAVIGATION_TIMEOUT_MS', '0')),
               request_timeout_seconds=float(os.getenv('TESTFLOW_REQUEST_TIMEOUT_SECONDS', '0')) or None,
               model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')))
    event(run_dir, state, 'run_started', selected=len(paths), auto_repair=auto_repair)
    if not no_ai and analyzer is None:
        try:
            analyzer = DeepSeek()
        except Exception as exc:
            state['notes'].append('AI unavailable: ' + redact(exc))
    stage = 'baseline' if baseline else 'initial'
    state[stage] = []
    report(run_dir, state)
    try:
        event(run_dir, state, 'stage_started', stage=stage)
        for i, path in enumerate(paths, 1):
            if baseline:
                path = root / 'baselines/raw_initial' / path.name
            print(f'[{stage} {i}/{len(paths)}] {path.name}', flush=True)
            event(run_dir, state, 'execution_started', stage=stage, test_id=path.stem.removeprefix('test_').upper())
            result = execute(path, run_dir / stage / path.stem, root, timeout)
            state[stage].append(result)
            event(run_dir, state, 'execution_finished', stage=stage, test_id=result['test_id'],
                  status=result['status'], classification=result['classification'], duration=result['duration'], evidence=result['directory'])
            print(f"  {result['status']} / {result['classification']}", flush=True)
            report(run_dir, state)
        event(run_dir, state, 'stage_finished', stage=stage, counts=summary(state[stage]))
        if analyzer is not None and not no_ai:
            event(run_dir, state, 'stage_started', stage='analysis_and_repair')
            for initial in state[stage]:
                if initial['status'] != 'failed':
                    continue
                current = initial
                for round_number in range(1, (rounds if auto_repair else 1) + 1):
                    print(f"[analysis] {current['test_id']} round {round_number}", flush=True)
                    directory = run_dir / 'repairs' / current['test_id'] / str(round_number)
                    directory.mkdir(parents=True, exist_ok=True)
                    event(run_dir, state, 'analysis_started', test_id=current['test_id'], round=round_number)
                    analysis_start = time.monotonic()
                    a = analyze(current, cases[current['test_id']], analyzer, directory)
                    attempt = {'test_id': current['test_id'], 'round': round_number,
                               'analysis': a, 'decision': 'suggestion_only',
                               'analysis_seconds': round(time.monotonic() - analysis_start, 3)}
                    state['attempts'].append(attempt)
                    event(run_dir, state, 'analysis_finished', test_id=current['test_id'], round=round_number,
                          category=a['category'], duration=attempt['analysis_seconds'], provider=a.get('provider'))
                    write_json(directory / 'analysis.json', a)
                    if auto_repair:
                        try:
                            attempt['patch'] = apply_repair(root, current, a, directory)
                            attempt['decision'] = 'applied'
                        except (Rejected, ValueError) as exc:
                            attempt.update(decision='human_review', reason=str(exc))
                            write_json(directory / 'decision.json', attempt)
                            event(run_dir, state, 'repair_decision', test_id=current['test_id'], round=round_number,
                                  decision=attempt['decision'], reason=attempt['reason'])
                            report(run_dir, state)
                            break
                        write_json(directory / 'decision.json', attempt)
                        event(run_dir, state, 'repair_decision', test_id=current['test_id'], round=round_number,
                              decision=attempt['decision'], patch=attempt['patch'])
                        event(run_dir, state, 'execution_started', stage='retest', test_id=current['test_id'], round=round_number)
                        current = execute(raw_target(root, Path(current['script']).name),
                                          directory / 'retest', root, timeout)
                        attempt['result'] = current
                        write_json(directory / 'decision.json', attempt)
                        event(run_dir, state, 'execution_finished', stage='retest', test_id=current['test_id'],
                              round=round_number, status=current['status'], duration=current['duration'], evidence=current['directory'])
                        if current['status'] == 'passed':
                            report(run_dir, state)
                            break
                    report(run_dir, state)
            event(run_dir, state, 'stage_finished', stage='analysis_and_repair')
        if any(a['decision'] == 'applied' for a in state['attempts']):
            # Always include ALL raw tests after any accepted repair, even when selection was narrow.
            all_paths, _ = select(root)
            state['regression'] = []
            state['regression_planned_count'] = len(all_paths)
            event(run_dir, state, 'stage_started', stage='regression', total=len(all_paths))
            for i, path in enumerate(all_paths, 1):
                print(f'[regression {i}/{len(all_paths)}] {path.name}', flush=True)
                event(run_dir, state, 'execution_started', stage='regression', test_id=path.stem.removeprefix('test_').upper())
                result = execute(path, run_dir / 'regression' / path.stem, root, timeout)
                state['regression'].append(result)
                event(run_dir, state, 'execution_finished', stage='regression', test_id=result['test_id'],
                      status=result['status'], duration=result['duration'], evidence=result['directory'])
                report(run_dir, state)
            event(run_dir, state, 'stage_finished', stage='regression', counts=summary(state['regression']))
        state['finished'] = True
    finally:
        state['ended_at_utc'] = now()
        protected_after = {name: hashes(root / name) for name in ('manual_tests', 'baselines')}
        state['protected_files_unchanged'] = protected_after == protected_before
        if not state['protected_files_unchanged']:
            state['notes'].append('ERROR: Protected files changed during execution; inspect before using results.')
        event(run_dir, state, 'run_finished' if state['finished'] else 'run_interrupted', protected_files_unchanged=state['protected_files_unchanged'])
        report(run_dir, state)
    print(f'Report: {run_dir / "report.md"}', flush=True)
    return run_dir, state


def analyze_saved(run_dir, analyzer=None):
    run_dir = Path(run_dir).resolve()
    state = json.loads((run_dir / 'run.json').read_text(encoding='utf-8'))
    root = Path(state['root'])
    cases = {c['test_id']: c for c in json.loads((root / 'generated_test_cases.json').read_text(encoding='utf-8'))}
    analyzer = analyzer or DeepSeek()
    # Preserve the original run and its analyses; a separate timestamped review is written.
    review = run_dir / ('review-' + uuid.uuid4().hex[:8])
    review.mkdir()
    analyses = []
    for result in state.get('regression', state.get('initial', state.get('baseline', []))):
        if result['status'] == 'failed':
            analyses.append({'test_id': result['test_id'], 'analysis': analyze(result, cases[result['test_id']], analyzer)})
    write_json(review / 'analysis.json', analyses)
    (review / 'report.md').write_text('\n\n'.join(
        f"## {a['test_id']}\n\n{a['analysis']['summary']}\n\n{a['analysis']['suggestion']}" for a in analyses), encoding='utf-8')
    return review
