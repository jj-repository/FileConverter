#!/usr/bin/env python
"""
Regenerate tests/matrix/known_gaps.py from the latest matrix JSON.

The matrix marks these known-failing pairs as xfail so the suite stays green
except for *new* regressions. When a gap is genuinely fixed, its case shows up
as XPASS — rerun this script to drop it from the baseline.

Usage:
    python scripts/run_matrix.py        # produces conversion-matrix.json
    python scripts/gen_known_gaps.py    # regenerates known_gaps.py
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "tests" / "matrix"


def short(detail: str) -> str:
    # First meaningful line, trimmed — enough to explain the gap.
    line = next((ln for ln in detail.splitlines() if ln.strip()), detail)
    return line.strip()[:120]


def main() -> int:
    data = json.loads((HERE / "conversion-matrix.json").read_text(encoding="utf-8"))
    fails = sorted(
        (
            (r["category"], r["in"], r["out"], short(r["detail"]))
            for r in data
            if r["status"] == "fail"
        ),
        key=lambda t: (t[0], t[1], t[2]),
    )
    lines = [
        '"""',
        "Baseline of known-failing conversion pairs (AUTO-GENERATED).",
        "",
        "Each entry is a pair the converter advertises in get_supported_formats()",
        "but cannot currently perform, with the captured error. The matrix xfails",
        "these so only NEW regressions turn the suite red. Fix the converter, rerun",
        "scripts/run_matrix.py then scripts/gen_known_gaps.py to shrink this list.",
        "",
        "Regenerate: python scripts/gen_known_gaps.py",
        '"""',
        "",
        "KNOWN_GAPS = {",
    ]
    for cat, i, o, reason in fails:
        reason_esc = reason.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    ("{cat}", "{i}", "{o}"): "{reason_esc}",')
    lines.append("}")
    lines.append("")
    out = HERE / "known_gaps.py"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(fails)} known gaps to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
