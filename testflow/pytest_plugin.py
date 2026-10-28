"""Loaded only inside an isolated execution subprocess, never for framework tests."""
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from .common import redact, write_json

_state = {}
_contexts = []
_traces = set()
_originals = []
AD_HOSTS = ('googlesyndication.com', 'doubleclick.net', 'googleadservices.com',
            'fundingchoicesmessages.google.com', 'googletagservices.com',
            'adtrafficquality.google', 'googletagmanager.com')


def is_ad_url(url):
    host = (urlsplit(url).hostname or '').lower()
    return any(host == domain or host.endswith('.' + domain) for domain in AD_HOSTS)


def navigation_timeout(requested, limit):
    return limit if requested is None or requested == 0 else min(requested, limit)


@pytest.fixture
def context(browser, browser_context_args):
    # Own this fixture's lifecycle so the standard plugin does not stop our trace
    # without a path before it can be saved. Script-local fixtures still override it.
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture
def page(context):
    return context.new_page()


def _save():
    write_json(Path(os.environ['TESTFLOW_EVIDENCE']) / 'pytest.json', _state)


def pytest_configure(config):
    directory = Path(os.environ['TESTFLOW_EVIDENCE'])
    directory.mkdir(parents=True, exist_ok=True)
    _state.update(tests={}, collection_errors=[], artifacts=[], evidence_errors=[], http=[], browser_events=[],
                  blocked_requests=[], block_ad_hosts=os.getenv('TESTFLOW_BLOCK_ADS') == '1',
                  vignette_guards=[],
                  request_timeout_seconds=float(os.getenv('TESTFLOW_REQUEST_TIMEOUT_SECONDS', '0')) or None,
                  navigation_timeout_ms=int(os.getenv('TESTFLOW_NAVIGATION_TIMEOUT_MS', '0')))
    _save()
    # Evidence collection preserves native request behavior by default. A limit is opt-in.
    try:
        import requests
        original = requests.sessions.Session.request

        def request(session, method, url, **kwargs):
            configured_timeout = _state['request_timeout_seconds']
            injected = configured_timeout is not None and 'timeout' not in kwargs
            if injected:
                kwargs['timeout'] = configured_timeout
            record = {'method': method, 'url': re.sub(r'([?&](?:email|password|token)=)[^&]*',
                                                    r'\1[REDACTED]', str(url)),
                      'timeout_seconds': kwargs.get('timeout'), 'timeout_injected': injected}
            started = time.monotonic()
            try:
                response = original(session, method, url, **kwargs)
                record['status_code'] = response.status_code
                # Only small public business status fields are recorded, not credentials or user bodies.
                try:
                    body = response.json()
                    if isinstance(body, dict):
                        record['business'] = {k: body[k] for k in ('responseCode', 'message') if k in body}
                except ValueError:
                    record['body_preview'] = response.text[:500]
                return response
            except Exception as exc:
                record['error'] = redact(exc)
                raise
            finally:
                record['duration_seconds'] = round(time.monotonic() - started, 3)
                _state['http'].append(record)
                _save()

        requests.sessions.Session.request = request
        _originals.append((requests.sessions.Session, 'request', original))
    except ImportError:
        pass
    try:
        from playwright.sync_api import Browser, BrowserContext, Page
        new_context, close = Browser.new_context, BrowserContext.close
        if _state['navigation_timeout_ms']:
            original_goto = Page.goto

            def goto(page, url, **kwargs):
                kwargs['timeout'] = navigation_timeout(kwargs.get('timeout'), _state['navigation_timeout_ms'])
                return original_goto(page, url, **kwargs)

            Page.goto = goto
            _originals.append((Page, 'goto', original_goto))

        def create(browser, *args, **kwargs):
            context = new_context(browser, *args, **kwargs)
            _contexts.append(context)
            if _state['block_ad_hosts']:
                def route_request(route):
                    if is_ad_url(route.request.url):
                        _state['blocked_requests'].append(route.request.url)
                        _save()
                        route.abort()
                    else:
                        route.continue_()
                context.route('**/*', route_request)
            def record(event, value):
                if len(_state['browser_events']) < 250:
                    _state['browser_events'].append({'event': event, 'value': redact(value)[:1500]})
                    _save()

            def page_created(page):
                page.on('console', lambda message: record('console', message.text))
                page.on('pageerror', lambda error: record('pageerror', error))
                page.on('requestfailed', lambda request: record('requestfailed', {'url': request.url, 'failure': request.failure}))
                page.on('domcontentloaded', lambda: record('domcontentloaded', page.url))
                if _state['block_ad_hosts']:
                    try:
                        page.add_init_script(
                            "(() => {"
                            "  const remove = () => {"
                            "    document.querySelectorAll('#google_vignette').forEach(el => el.remove());"
                            "  };"
                            "  const watch = () => {"
                            "    remove();"
                            "    if (document.documentElement) {"
                            "      new MutationObserver(remove).observe(document.documentElement, {childList: true, subtree: true});"
                            "    }"
                            "  };"
                            "  if (document.documentElement) {"
                            "    watch();"
                            "  } else {"
                            "    document.addEventListener('DOMContentLoaded', watch, {once: true});"
                            "  }"
                            "})();"
                        )
                        _state['vignette_guards'].append(page.url or 'about:blank')
                        _save()
                    except Exception as exc:
                        _state['evidence_errors'].append(redact(exc))
                        _save()
            context.on('page', page_created)
            try:
                context.tracing.start(screenshots=True, snapshots=True, sources=True)
                _traces.add(id(context))
            except Exception as exc:
                _state['evidence_errors'].append(redact(exc))
            return context

        def finish(context, *args, **kwargs):
            _capture(context)
            return close(context, *args, **kwargs)

        Browser.new_context, BrowserContext.close = create, finish
        _originals.extend([(Browser, 'new_context', new_context), (BrowserContext, 'close', close)])
    except ImportError:
        _state['evidence_errors'].append('Playwright unavailable; browser evidence cannot be captured')


def _capture(context):
    if id(context) not in _traces:
        return
    path = Path(os.environ['TESTFLOW_EVIDENCE']) / f'trace-{_contexts.index(context)}.zip'
    try:
        context.tracing.stop(path=str(path))
        _state['artifacts'].append(str(path))
    except Exception as exc:
        _state['evidence_errors'].append(redact(exc))
    finally:
        _traces.discard(id(context))
        _save()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    phases = _state['tests'].setdefault(report.nodeid, [])
    phases.append({'phase': report.when, 'outcome': report.outcome,
                   'duration': report.duration, 'error': str(report.longrepr) if report.failed or report.skipped else '',
                   'sections': [{'name': title, 'text': content} for title, content in report.sections]})
    if report.failed:
        for ci, context in enumerate(_contexts):
            try:
                for pi, page in enumerate(context.pages):
                    if not page.is_closed():
                        base = Path(os.environ['TESTFLOW_EVIDENCE']) / f'failure-{len(_state["tests"])}-{report.when}-{ci}-{pi}'
                        try:
                            page.screenshot(path=str(base.with_suffix('.png')), timeout=5000)
                            _state['artifacts'].append(str(base.with_suffix('.png')))
                        except Exception as exc:
                            _state['evidence_errors'].append(redact(exc))
                        try:
                            base.with_suffix('.html').write_text(page.content(), encoding='utf-8')
                            _state['artifacts'].append(str(base.with_suffix('.html')))
                        except Exception as exc:
                            _state['evidence_errors'].append(redact(exc))
            except Exception as exc:
                _state['evidence_errors'].append(redact(exc))
    _save()


def pytest_collectreport(report):
    if report.failed:
        _state['collection_errors'].append({'nodeid': report.nodeid, 'error': str(report.longrepr)})
        _save()


def pytest_runtest_logstart(nodeid, location):
    _state['current_test'] = nodeid
    _save()


def pytest_sessionfinish(session, exitstatus):
    for context in _contexts:
        _capture(context)
    _state['exit_code'] = int(exitstatus)
    _save()


def pytest_unconfigure(config):
    for owner, name, original in reversed(_originals):
        setattr(owner, name, original)
