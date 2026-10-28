import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'generated_tests' / 'case_raw'


def load_environment(root=ROOT):
    """Read simple KEY=value .env entries without executing shell content."""
    path = Path(root) / '.env'
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key, value = key.strip(), value.strip()
            if re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                os.environ.setdefault(key, value)
    # An already-running desktop app may not inherit newly saved Windows user variables.
    if os.name == 'nt' and not os.getenv('DEEPSEEK_API_KEY'):
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as key:
                value, _ = winreg.QueryValueEx(key, 'DEEPSEEK_API_KEY')
                if isinstance(value, str) and value:
                    os.environ['DEEPSEEK_API_KEY'] = value
        except OSError:
            pass


def redact(value):
    text = str(value)
    key = os.getenv('DEEPSEEK_API_KEY')
    return text.replace(key, '[REDACTED_API_KEY]') if key else text


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(redact(json.dumps(value, ensure_ascii=False, indent=2)), encoding='utf-8')
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def raw_target(root, name):
    root = Path(root).resolve()
    if not re.fullmatch(r'test_tc_\d{3}\.py', name):
        raise ValueError('Only existing test_tc_NNN.py files can be repaired')
    directory = root / 'generated_tests' / 'case_raw'
    target = directory / name
    if ((root / 'generated_tests').is_symlink() or directory.is_symlink() or target.is_symlink()
            or not directory.resolve().is_relative_to(root) or target.resolve().parent != directory.resolve()):
        raise ValueError('Repair target must be a regular file inside case_raw')
    if not target.is_file():
        raise ValueError('Repair target does not exist')
    return target
