"""
Baseline of known-failing conversion pairs (AUTO-GENERATED).

Each entry is a pair the converter advertises in get_supported_formats()
but cannot currently perform, with the captured error. The matrix xfails
these so only NEW regressions turn the suite red. Fix the converter, rerun
scripts/run_matrix.py then scripts/gen_known_gaps.py to shrink this list.

Regenerate: python scripts/gen_known_gaps.py
"""

KNOWN_GAPS = {
}
