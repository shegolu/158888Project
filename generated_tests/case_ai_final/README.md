# Final code for 17 comparison cases

This directory contains byte-for-byte copies of existing files. Tests were neither regenerated nor rewritten.

- 15 AI repair candidates: TC_001, TC_005, TC_006, TC_010, TC_012, TC_013, TC_014, TC_015, TC_017, TC_018, TC_019, TC_022, TC_023, TC_025 and TC_026.
- TC_007: the patched version from `runs/manual_patch_TC_007/after.py`; this archive does not establish an AI repair source.
- TC_028: no separate AI repair candidate was found; the unmodified AI-generated working version is retained.

`sources.json` records the original path, version type and SHA-256 for each file. References to `runs/` identify local source records that are excluded from this source delivery. Initially generated versions are in `baselines/raw_initial/`, and corresponding manual versions are in `manual_tests/`.

This directory is a comparison archive. Execution and repair tools use `generated_tests/case_raw/`.
