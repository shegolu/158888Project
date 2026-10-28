import hashlib
import json
import shutil
from pathlib import Path


def hashes(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob('*')) if p.is_file()}


def prepare(root):
    root = Path(root).resolve()
    raw = root / 'generated_tests' / 'case_raw'
    manual = root / 'manual_tests'
    baseline = root / 'baselines' / 'raw_initial'
    if not raw.is_dir():
        raise ValueError(f'Missing raw directory: {raw}')
    for p in [raw, manual, baseline, *raw.rglob('*')]:
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError(f'Unexpected link or path outside project: {p}')
    sources = sorted((root / 'generated_tests').glob('test_tc_*.py'))
    for p in sources:
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError(f'Unexpected source link: {p}')
        if (manual / p.name).exists():
            raise ValueError(f'Refusing to overwrite manual file: {manual / p.name}')
    # The snapshot is never refreshed, including on subsequent CLI invocations.
    if not baseline.exists():
        baseline.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(raw, baseline)
        if hashes(raw) != hashes(baseline):
            raise RuntimeError('Baseline copy verification failed; no manual files moved')
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    manual.mkdir(exist_ok=True)
    for p in sources:
        shutil.move(str(p), str(manual / p.name))
    for name, digest in before.items():
        if hashlib.sha256((manual / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Manual file verification failed: {name}')
    manifest = root / 'baselines' / 'preservation.json'
    if not manifest.exists():
        manifest.write_text(json.dumps({'baseline': hashes(baseline),
                                      'manual': hashes(manual)}, indent=2), encoding='utf-8')
    return {'moved': len(sources), 'baseline_files': len(hashes(baseline)),
            'manual_files': len(hashes(manual))}
