import json
from pathlib import Path

import pytest

from testflow.common import raw_target
from testflow.guard import Rejected, validate
from testflow.layout import hashes, prepare
from testflow.pipeline import analyze_saved, apply_repair, run
from testflow.runner import classify, execute, select


SOURCE = '''def test_ui(page):
    page.set_content("<button id='ready'>Ready</button>")
    page.locator("#wrong").click(timeout=2000)
    assert page.locator("#ready").inner_text() == "Ready"
'''


def project(tmp_path, source=SOURCE):
    raw = tmp_path / 'generated_tests/case_raw'
    raw.mkdir(parents=True)
    (raw / 'test_tc_001.py').write_text(source, encoding='utf-8')
    (tmp_path / 'generated_tests/test_tc_001.py').write_bytes(b'# independent human version\r\n')
    (tmp_path / 'generated_test_cases.json').write_text(json.dumps([
        {'test_id': 'TC_001', 'test_type': 'UI', 'expected_result': 'Ready button is clickable'}]), encoding='utf-8')
    return tmp_path


def proposal(source=SOURCE):
    return {'category': 'locator', 'summary': 'Wrong selector',
            'evidence': ['DOM has #ready and no #wrong'], 'suggestion': 'Use #ready',
            'confidence': 0.99, 'safe_to_repair': True,
            'repaired_code': source.replace('#wrong', '#ready')}


def test_preservation_is_idempotent_and_byte_exact(tmp_path):
    root = project(tmp_path)
    original = (root / 'generated_tests/test_tc_001.py').read_bytes()
    assert prepare(root)['moved'] == 1
    assert (root / 'manual_tests/test_tc_001.py').read_bytes() == original
    baseline = hashes(root / 'baselines')
    (root / 'generated_tests/case_raw/test_tc_001.py').write_text('# changed')
    assert prepare(root)['moved'] == 0
    assert hashes(root / 'baselines') == baseline


def test_refuses_manual_overwrite(tmp_path):
    root = project(tmp_path)
    (root / 'manual_tests').mkdir()
    (root / 'manual_tests/test_tc_001.py').write_text('keep')
    with pytest.raises(ValueError):
        prepare(root)
    assert (root / 'generated_tests/test_tc_001.py').exists()


def test_locator_repair_and_setup_are_allowed():
    assert validate(SOURCE, proposal()['repaired_code'])
    before = 'def test_x(page):\n    page.goto("https://example.com")\n    assert 2 == 2\n'
    after = before.replace('    assert', '    page.locator("#user").fill("user")\n    assert')
    assert validate(before, after)


@pytest.mark.parametrize('bad', [
    SOURCE.replace('    assert page.locator("#ready").inner_text() == "Ready"', '    assert True'),
    SOURCE.replace(' == "Ready"', ' != "Missing"'),
    SOURCE.replace('    assert', '    return\n    assert'),
    SOURCE.replace('def test_ui', '@pytest.mark.skip\ndef test_ui'),
    SOURCE.replace('    assert', '    pytest.xfail("ignore")\n    assert'),
    SOURCE.replace('    assert', '    page = object()\n    assert'),
    SOURCE.replace('    assert', '    open("outside", "w").write("bad")\n    assert'),
    SOURCE.replace('    assert', '    page.evaluate("document.body.innerHTML = 1")\n    assert'),
    SOURCE.replace('    assert', '    try:\n        assert False\n    except Exception:\n        pass\n    assert'),
    SOURCE.replace('    assert', '    if False:\n        return\n    assert'),
    SOURCE.replace('    assert', '    import os\n    assert'),
    SOURCE.replace('click(timeout=2000)', 'click(timeout=0)'),
    SOURCE.replace('.locator("#wrong")', '.locator("#wrong").nth(__import__("os").system("bad"))'),
    'def broken(',
])
def test_rejects_assertion_bypass_and_unrelated_edits(bad):
    with pytest.raises(Rejected):
        validate(SOURCE, bad)


def test_api_response_cannot_be_hardcoded():
    code = 'import requests\ndef test_api():\n    response = requests.get("https://example.com")\n    assert response.status_code == 200\n'
    with pytest.raises(Rejected):
        validate(code, code.replace('requests.get("https://example.com")', 'type("Fake", (), {"status_code": 200})()'))


@pytest.mark.parametrize('before,after', [
    ('def test_x(page):\n    expect(page.locator("#success")).to_be_visible()\n',
     'def test_x(page):\n    expect(page.locator("body")).to_be_visible()\n'),
    ('def test_x(page):\n    success = page.locator("#success")\n    text = success.inner_text()\n    assert text == "ok"\n',
     'def test_x(page):\n    success = page.locator("body")\n    text = success.inner_text()\n    assert text == "ok"\n'),
])
def test_assertion_locator_and_transitive_dependencies_cannot_be_weakened(before, after):
    with pytest.raises(Rejected):
        validate(before, after)


def test_path_and_stale_source_guards(tmp_path):
    root = project(tmp_path)
    with pytest.raises(ValueError):
        raw_target(root, '../../manual_tests/test_tc_001.py')
    prepare(root)
    result = {'script': str(root / 'generated_tests/case_raw/test_tc_001.py'),
              'source_sha256': 'stale', 'classification': 'test_failure'}
    with pytest.raises(Rejected, match='changed since'):
        apply_repair(root, result, proposal(), root / 'proposal')


@pytest.mark.parametrize('error,phase,expected', [
    ("ModuleNotFoundError: No module named 'playwright'", 'collection', 'environment'),
    ('net::ERR_NAME_NOT_RESOLVED', 'call', 'environment'),
    ('requests.exceptions.ReadTimeout', 'call', 'environment'),
    ('Page.goto: Timeout 100000ms exceeded', 'setup', 'environment'),
    ("No module named 'generated_tests.test_tc_004'", 'collection', 'collection'),
    ('locator.click: Timeout 30000ms exceeded', 'call', 'test_failure'),
    ('fixture account not found', 'setup', 'preparation'),
])
def test_failure_categories(error, phase, expected):
    assert classify(error, phase) == expected


def test_selection_validates_missing_and_unknown_cases(tmp_path):
    root = project(tmp_path)
    assert len(select(root, 'ui', ['TC_001'])[0]) == 1
    with pytest.raises(ValueError):
        select(root, 'api')
    with pytest.raises(ValueError):
        select(root, ids=['TC_999'])


def test_real_offline_browser_repair_loop(tmp_path):
    root = project(tmp_path)

    class FakeAnalyzer:
        def analyze(self, result, case):
            assert '#wrong' in Path(result['source_snapshot']).read_text(encoding='utf-8')
            assert result['evidence']['artifacts']
            return proposal()

    directory, state = run(root, auto_repair=True, analyzer=FakeAnalyzer(), timeout=30)
    assert state['initial'][0]['status'] == 'failed'
    assert state['attempts'][0]['decision'] == 'applied'
    assert state['attempts'][0]['result']['status'] == 'passed'
    assert state['regression'][0]['status'] == 'passed'
    assert state['protected_files_unchanged']
    assert any(p.endswith('.png') for p in state['initial'][0]['evidence']['artifacts'])
    assert any(p.endswith('.zip') for p in state['initial'][0]['evidence']['artifacts'])
    assert (directory / 'report.md').is_file()
    metrics = json.loads((directory / 'metrics.json').read_text(encoding='utf-8'))
    assert metrics['initial']['failed'] == 1
    assert metrics['modified_cases'] == 1
    assert metrics['modified_retest_passed'] == 1
    assert metrics['regression']['passed'] == 1
    assert (directory / 'cases.csv').read_text(encoding='utf-8-sig').count('TC_001') == 1
    events = [json.loads(line) for line in (directory / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
    assert events[0]['event'] == 'run_started'
    assert events[-1]['event'] == 'run_finished'
    assert any(e['event'] == 'repair_decision' for e in events)
    assert (directory / 'repairs/TC_001/1/decision.json').is_file()
    assert (directory / 'inputs/raw/test_tc_001.py').read_text(encoding='utf-8') == SOURCE
    assert '#wrong' in (root / 'baselines/raw_initial/test_tc_001.py').read_text()


def test_run_only_does_not_call_ai_and_preserves_files(tmp_path):
    root = project(tmp_path, 'def test_ok():\n    assert 2 + 2 == 4\n')
    _, state = run(root, no_ai=True, timeout=20)
    assert state['initial'][0]['status'] == 'passed'
    assert state['attempts'] == []
    assert state['protected_files_unchanged']


def test_collection_setup_and_timeout_have_structured_evidence(tmp_path):
    root = project(tmp_path, 'def broken(:\n')
    script = root / 'generated_tests/case_raw/test_tc_001.py'
    result = execute(script, root / 'collect', root, timeout=20)
    assert result['phase'] == 'collection'
    script.write_text('import pytest\n@pytest.fixture\ndef value():\n    raise RuntimeError("missing data")\ndef test_x(value):\n    assert value\n')
    result = execute(script, root / 'setup', root, timeout=20)
    assert result['classification'] == 'preparation'
    script.write_text('import time\ndef test_hang():\n    time.sleep(10)\n')
    result = execute(script, root / 'timeout', root, timeout=2)
    assert result['timed_out']
    assert result['classification'] == 'execution_error'
    assert Path(result['process_log']).is_file()


def test_repair_round_limit_and_invalid_ai(tmp_path):
    root = project(tmp_path, 'def test_x():\n    assert False\n')

    class BadAnalyzer:
        def analyze(self, result, case):
            return {'category': 'invented'}

    _, state = run(root, auto_repair=True, analyzer=BadAnalyzer(), timeout=20)
    assert len(state['attempts']) == 1
    assert state['attempts'][0]['decision'] == 'human_review'
    assert state['protected_files_unchanged']
    with pytest.raises(ValueError):
        run(root, rounds=3)


def test_two_round_limit_and_full_regression_after_narrow_selection(tmp_path, monkeypatch):
    from testflow import pipeline
    from testflow.common import digest
    root = project(tmp_path)
    second = root / 'generated_tests/case_raw/test_tc_002.py'
    second.write_text('def test_other():\n    assert True\n')
    cases = json.loads((root / 'generated_test_cases.json').read_text())
    cases.append({'test_id': 'TC_002', 'test_type': 'UI'})
    (root / 'generated_test_cases.json').write_text(json.dumps(cases))
    calls = []

    def fake_execute(script, directory, root, timeout):
        directory = Path(directory)
        directory.mkdir(parents=True)
        snapshot = directory / 'source.py'
        snapshot.write_bytes(Path(script).read_bytes())
        calls.append(Path(script).name)
        return {'test_id': Path(script).stem.removeprefix('test_').upper(),
                'script': str(script), 'source_sha256': digest(script), 'source_snapshot': str(snapshot),
                'status': 'failed', 'phase': 'call', 'classification': 'test_failure',
                'duration': 0.1, 'directory': str(directory), 'data_risks': []}

    class ChangingAnalyzer:
        def analyze(self, result, case):
            text = Path(result['source_snapshot']).read_text()
            a = proposal(text)
            a['repaired_code'] = text.replace('#wrong', '#next') if '#wrong' in text else text.replace('#next', '#last')
            return a

    monkeypatch.setattr(pipeline, 'execute', fake_execute)
    _, state = run(root, ids=['TC_001'], auto_repair=True, analyzer=ChangingAnalyzer())
    assert len(state['attempts']) == 2
    assert all(a['decision'] == 'applied' for a in state['attempts'])
    assert len(state['regression']) == 2
    assert calls.count('test_tc_001.py') == 4  # initial, two retries, full regression
    assert calls.count('test_tc_002.py') == 1
    assert state['latest_summary']['failed'] == 2


def test_offline_analysis_uses_snapshot_and_writes_separate_review(tmp_path):
    root = project(tmp_path, 'def test_fail():\n    assert False\n')
    directory, _ = run(root, no_ai=True, timeout=20)
    original_run = (directory / 'run.json').read_bytes()
    class Analyzer:
        def analyze(self, result, case):
            a = proposal()
            a.update(category='expected_result', safe_to_repair=False, repaired_code=None)
            return a
    review = analyze_saved(directory, Analyzer())
    assert (review / 'analysis.json').is_file()
    assert (directory / 'run.json').read_bytes() == original_run


def test_fixed_baseline_execution_does_not_write_snapshot(tmp_path):
    root = project(tmp_path, 'def test_ok():\n    assert 1 == 1\n')
    _, state = run(root, baseline=True, no_ai=True, timeout=20)
    assert state['baseline'][0]['status'] == 'passed'
    assert state['protected_files_unchanged']
    assert not list((root / 'baselines/raw_initial').rglob('*.pyc'))


@pytest.mark.parametrize('url,expected', [
    ('https://pagead2.googlesyndication.com/pagead/test', True),
    ('https://fundingchoicesmessages.google.com/test', True),
    ('https://googlesyndication.com.evil.example/test', False),
    ('https://automationexercise.com/products', False),
    ('https://ajax.googleapis.com/ajax/libs/jquery.min.js', False),
])
def test_ad_profile_preserves_site_and_functional_resources(url, expected):
    from testflow.pytest_plugin import is_ad_url
    assert is_ad_url(url) is expected


@pytest.mark.parametrize('requested,limit,expected', [(100000, 30000, 30000), (5000, 30000, 5000), (None, 30000, 30000), (0, 30000, 30000)])
def test_explicit_navigation_budget_preserves_shorter_timeouts(requested, limit, expected):
    from testflow.pytest_plugin import navigation_timeout
    assert navigation_timeout(requested, limit) == expected


@pytest.mark.parametrize('budget,explicit,status,injected', [
    (None, None, 'passed', False),
    (0.05, None, 'failed', True),
    (1, 0.05, 'failed', False),
])
def test_request_timing_is_preserved_unless_explicitly_configured(tmp_path, monkeypatch, budget, explicit, status, injected):
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(0.25)
            self.send_response(200)
            self.end_headers()
            try:
                self.wfile.write(b'{"ready": true}')
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # Expected only when the client deliberately times out.

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv('TESTFLOW_REQUEST_TIMEOUT_SECONDS', str(budget or 0))
        argument = '' if explicit is None else f', timeout={explicit}'
        root = project(tmp_path, 'import requests\ndef test_request():\n'
                       f'    response = requests.get("http://127.0.0.1:{server.server_port}/"{argument})\n'
                       '    assert response.json()["ready"] is True\n')
        result = execute(root / 'generated_tests/case_raw/test_tc_001.py', root / 'evidence', root, 20)
        assert result['status'] == status
        request = result['evidence']['http'][0]
        assert request['timeout_injected'] is injected
        assert request['timeout_seconds'] == (explicit if explicit is not None else budget)
        assert request['duration_seconds'] > 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_explicit_overload_evidence_is_environment_but_generic_503_is_not(tmp_path):
    assert classify('JSONDecodeError', 'call', {'http': [
        {'status_code': 503, 'body_preview': 'This website is under heavy load (queue full)'}
    ]}) == 'environment'
    assert classify('AssertionError', 'call', {'http': [
        {'status_code': 503, 'body_preview': 'Application error'}
    ]}) == 'test_failure'
    html = tmp_path / 'failure.html'
    html.write_text('<html>This website is under heavy load (queue full)</html>')
    assert classify('locator not found', 'call', {'artifacts': [str(html)]}) == 'environment'


def test_interrupted_report_marks_partial_regression(tmp_path):
    from testflow.records import export
    state = {'run_id': 'interrupted', 'finished': False, 'interrupted': True,
             'interruption_reason': 'Stopped for diagnosis', 'regression_planned_count': 42}
    export(tmp_path, state)
    report = (tmp_path / 'summary_zh.md').read_text(encoding='utf-8')
    assert '已中断' in report
    assert '0/42' in report
    assert '执行失败数不等于脚本缺陷数' in report
