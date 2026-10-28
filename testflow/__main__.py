import argparse
import math
import os
from pathlib import Path

from .common import ROOT, load_environment
from .pipeline import analyze_saved, run


def main():
    parser = argparse.ArgumentParser(description='Run generated tests, capture evidence and optionally repair safely')
    commands = parser.add_subparsers(dest='command', required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--type', choices=['all', 'ui', 'api'], default='all')
    execute.add_argument('--ids', nargs='+', help='Example: TC_007 TC_029')
    execute.add_argument('--no-ai', action='store_true', help='Execute only; no model calls')
    execute.add_argument('--auto-repair', action='store_true', help='Opt into guarded edits and full regression')
    execute.add_argument('--max-rounds', type=int, choices=[1, 2], default=2)
    execute.add_argument('--timeout', type=int, default=120, help='Per-script wall-clock limit in seconds')
    execute.add_argument('--baseline', action='store_true', help='Execute the fixed snapshot without editing it')
    execute.add_argument('--block-ads', action='store_true', help='Block known third-party ad hosts and record the setting')
    execute.add_argument('--navigation-timeout', type=int, help='Optional cap per page.goto in milliseconds; recorded in environment')
    execute.add_argument('--request-timeout', type=float, help='Opt-in requests timeout in seconds when the script omits one; default preserves script behavior')
    review = commands.add_parser('analyze')
    review.add_argument('--run', required=True, type=Path, help='Existing runs/<run_id> directory')
    args = parser.parse_args()
    load_environment()
    # Prevent two CLI instances racing while repairing the same source files.
    lock = ROOT / '.testflow.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        parser.exit(2, 'Another workflow owns .testflow.lock. If interrupted, verify no workflow is running before removing it.\n')
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(str(os.getpid()))
        if args.command == 'analyze':
            print('Saved review:', analyze_saved(args.run))
            return 0
        if args.timeout <= 0:
            parser.error('--timeout must be positive')
        os.environ['TESTFLOW_BLOCK_ADS'] = '1' if args.block_ads else '0'
        if args.navigation_timeout is not None and args.navigation_timeout <= 0:
            parser.error('--navigation-timeout must be positive')
        os.environ['TESTFLOW_NAVIGATION_TIMEOUT_MS'] = str(args.navigation_timeout or 0)
        if args.request_timeout is not None and (not math.isfinite(args.request_timeout) or args.request_timeout <= 0):
            parser.error('--request-timeout must be finite and positive')
        os.environ['TESTFLOW_REQUEST_TIMEOUT_SECONDS'] = str(args.request_timeout or 0)
        _, state = run(kind=args.type, ids=args.ids, no_ai=args.no_ai,
                       auto_repair=args.auto_repair, rounds=args.max_rounds,
                       timeout=args.timeout, baseline=args.baseline)
        return 0 if (state['finished'] and state['protected_files_unchanged']
                     and state['latest_summary']['passed'] == state['latest_summary']['total']) else 1
    except (ValueError, OSError) as exc:
        parser.exit(2, str(exc) + '\n')
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    raise SystemExit(main())
