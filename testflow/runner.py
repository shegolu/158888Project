import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .common import ROOT, digest, redact, write_json


def audit(source):
    """Flag state dependencies without changing the test or silently seeding shared accounts."""
    risks = []
    if any(s in source for s in ('login-email', 'verifyLogin', 'getUserDetailByEmail')):
        risks.append('Requires an existing account; no per-test account provisioning is present.')
    if any(s in source for s in ('createAccount', "signup-email")):
        risks.append('Registration may collide with fixed email data; verify cleanup and uniqueness.')
    if any(s in source for s in ('deleteAccount', 'updateAccount', '/delete_account')):
        risks.append('Mutates account state; independent setup/cleanup must be verified.')
    if 'logout' in source and 'login-password' not in source:
        risks.append('Logout precondition may assume an authenticated browser context.')
    if 'set_input_files' in source:
        risks.append('Requires a real upload file relative to the project working directory.')
    return risks


def overload_evidence(evidence):
    """Recognize an explicit overload response, not arbitrary application 5xx errors."""
    markers = ('this website is under heavy load', 'queue full')
    reasons = []
    for response in evidence.get('http', []):
        if response.get('status_code') == 503 and any(
                marker in response.get('body_preview', '').lower() for marker in markers):
            reasons.append('HTTP 503: website explicitly reports overload')
    for artifact in evidence.get('artifacts', []):
        path = Path(artifact)
        if path.suffix == '.html' and path.is_file():
            with path.open(encoding='utf-8', errors='replace') as stream:
                html = stream.read(2_000_000).lower()
            if any(marker in html for marker in markers):
                reasons.append('Captured page explicitly reports website overload: ' + str(path))
    return reasons


def classify(error, phase, evidence=None):
    text = error.lower()
    if evidence and overload_evidence(evidence):
        return 'environment'
    environment = ('no module named \'requests\'', 'no module named \'playwright\'',
                   'no module named \'pytest', 'executable doesn\'t exist', 'playwright install',
                   'net::err_', 'connectionerror', 'connecttimeout', 'readtimeout',
                   'sslerror', 'getaddrinfo failed', 'proxyerror', 'modulenotfounderror: no module named \'openai')
    if any(s in text for s in environment):
        return 'environment'
    if 'page.goto: timeout' in text:
        return 'environment'  # Navigation never became ready; do not infer a script defect.
    if phase == 'collection':
        return 'collection'
    if phase in ('setup', 'teardown'):
        return 'preparation'
    if phase == 'process':
        return 'execution_error'
    return 'test_failure'  # A symptom, not a claim that the script or website is defective.


def execute(script, directory, root=ROOT, timeout=120):
    script, directory, root = Path(script).resolve(), Path(directory).resolve(), Path(root).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    snapshot = directory / 'source.py'
    snapshot.write_bytes(script.read_bytes())
    env = os.environ.copy()
    env['TESTFLOW_EVIDENCE'] = str(directory)
    env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    env.pop('PYTEST_ADDOPTS', None)
    env.pop('PYTEST_PLUGINS', None)
    command = [sys.executable, '-m', 'pytest', '-c', str(ROOT / 'pytest.ini'),
               '--rootdir', str(root), '--import-mode=importlib',
               '-p', 'pytest_playwright.pytest_playwright', '-p', 'testflow.pytest_plugin',
               '-o', 'addopts=', '-o', 'cache_dir=' + str(directory / 'cache'),
               '--tb=long', '-v', str(script)]
    start = time.monotonic()
    timed_out, process_error, code = False, '', None
    log = directory / 'process.log'
    with log.open('w', encoding='utf-8') as stream:
        try:
            process = subprocess.Popen(command, cwd=root, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=os.name != 'nt')
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                                   capture_output=True, timeout=15)
                else:
                    import signal
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=15)
                code = process.returncode
        except (OSError, subprocess.SubprocessError) as exc:
            process_error = redact(exc)
    log_text = redact(log.read_text(encoding='utf-8', errors='replace'))
    log.write_text(log_text, encoding='utf-8')
    evidence_file = directory / 'pytest.json'
    evidence = json.loads(evidence_file.read_text(encoding='utf-8')) if evidence_file.exists() else {}
    phases = [p for records in evidence.get('tests', {}).values() for p in records]
    failed = [p for p in phases if p['outcome'] == 'failed']
    skipped = any(p['outcome'] == 'skipped' for p in phases)
    error = '\n'.join(p['error'] for p in failed)
    if evidence.get('collection_errors'):
        phase = 'collection'
        error = '\n'.join(p['error'] for p in evidence['collection_errors'])
    elif failed:
        phase = failed[0]['phase']
    else:
        phase = 'call' if phases else 'process'
    if timed_out or process_error:
        phase = 'process'
        error = ('Per-script process timeout; inspect partial evidence.' if timed_out else process_error) + '\n' + error
    status = 'passed' if code == 0 and phases and not failed and not skipped else (
        'skipped' if skipped and not failed and code == 0 else 'failed')
    if not error and status == 'failed':
        error = log_text[-20000:]
    result = {'test_id': script.stem.removeprefix('test_').upper(), 'script': str(script),
              'source_snapshot': str(snapshot), 'source_sha256': digest(snapshot),
              'status': status, 'phase': phase, 'classification': classify(error, phase, evidence) if status == 'failed' else status,
              'environmental_observations': overload_evidence(evidence),
              'duration': round(time.monotonic() - start, 3), 'exit_code': code, 'timed_out': timed_out,
              'error': redact(error), 'process_log': str(log), 'evidence': evidence,
              'data_risks': audit(snapshot.read_text(encoding='utf-8')), 'directory': str(directory)}
    write_json(directory / 'result.json', result)
    return result


def select(root, kind='all', ids=None):
    root = Path(root)
    cases = json.loads((root / 'generated_test_cases.json').read_text(encoding='utf-8'))
    mapping = {c['test_id'].upper(): c for c in cases}
    requested = {s.upper() for s in ids or []}
    unknown = requested - mapping.keys()
    if unknown:
        raise ValueError(f'Unknown case IDs: {sorted(unknown)}')
    paths = []
    for test_id, case in sorted(mapping.items()):
        if requested and test_id not in requested:
            continue
        if kind != 'all' and case['test_type'].lower() != kind:
            continue
        path = root / 'generated_tests' / 'case_raw' / f'test_{test_id.lower()}.py'
        if not path.is_file():
            raise ValueError(f'Missing script for {test_id}: {path}')
        paths.append(path)
    if not paths:
        raise ValueError('Selection contains no tests')
    return paths, mapping
