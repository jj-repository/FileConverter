"""
Fixtures + reporting for the conversion matrix.

The matrix records every (category, input_format, output_format) attempt and,
at session end, writes a human-readable grid to ``conversion-matrix.md`` and
prints a summary to the terminal. Genuine conversion failures also fail their
individual pytest case so they show up in normal output and CI.
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Type

import pytest

from app.services.archive_converter import ArchiveConverter
from app.services.audio_converter import AudioConverter
from app.services.base_converter import BaseConverter
from app.services.data_converter import DataConverter
from app.services.document_converter import DocumentConverter
from app.services.ebook_converter import EbookConverter
from app.services.font_converter import FontConverter
from app.services.image_converter import ImageConverter
from app.services.spreadsheet_converter import SpreadsheetConverter
from app.services.subtitle_converter import SubtitleConverter
from app.services.video_converter import VideoConverter

# Category -> converter class. Single source of truth for the whole matrix.
CONVERTERS: Dict[str, Type[BaseConverter]] = {
    "image": ImageConverter,
    "video": VideoConverter,
    "audio": AudioConverter,
    "document": DocumentConverter,
    "data": DataConverter,
    "archive": ArchiveConverter,
    "spreadsheet": SpreadsheetConverter,
    "subtitle": SubtitleConverter,
    "ebook": EbookConverter,
    "font": FontConverter,
}

_SYMBOL = {"pass": "✓", "fail": "✗", "skip": "·"}


@dataclass
class Result:
    category: str
    in_fmt: str
    out_fmt: str
    status: str  # pass | fail | skip
    detail: str = ""


@dataclass
class Recorder:
    results: List[Result] = field(default_factory=list)

    def record(self, category, in_fmt, out_fmt, status, detail=""):
        self.results.append(Result(category, in_fmt, out_fmt, status, str(detail)[:200]))

    # -- reporting ---------------------------------------------------------

    def _formats(self, category):
        ins = sorted({r.in_fmt for r in self.results if r.category == category})
        outs = sorted({r.out_fmt for r in self.results if r.category == category})
        return ins, outs

    def _lookup(self, category, in_fmt, out_fmt):
        for r in self.results:
            if r.category == category and r.in_fmt == in_fmt and r.out_fmt == out_fmt:
                return r
        return None

    def markdown(self) -> str:
        passes = sum(r.status == "pass" for r in self.results)
        fails = sum(r.status == "fail" for r in self.results)
        skips = sum(r.status == "skip" for r in self.results)
        total = len(self.results)
        lines = [
            "# Conversion Matrix Report",
            "",
            f"**{passes} passed · {fails} failed · {skips} skipped** "
            f"out of {total} declared conversion pairs.",
            "",
            "Legend: ✓ pass · ✗ fail · · skipped (no input sample) · "
            "blank = not a declared pair. Rows = input format, columns = output format.",
            "",
        ]
        for category in sorted({r.category for r in self.results}):
            ins, outs = self._formats(category)
            lines.append(f"## {category}")
            lines.append("")
            lines.append("| in \\ out | " + " | ".join(outs) + " |")
            lines.append("|" + "---|" * (len(outs) + 1))
            for i in ins:
                cells = []
                for o in outs:
                    r = self._lookup(category, i, o)
                    cells.append(_SYMBOL.get(r.status, "") if r else "")
                lines.append(f"| **{i}** | " + " | ".join(cells) + " |")
            lines.append("")
            # Failure detail for this category
            cat_fails = [r for r in self.results if r.category == category and r.status == "fail"]
            if cat_fails:
                lines.append(f"### {category} failures")
                lines.append("")
                for r in cat_fails:
                    lines.append(f"- `{r.in_fmt} → {r.out_fmt}`: {r.detail}")
                lines.append("")
        return "\n".join(lines)

    def console_summary(self) -> str:
        passes = sum(r.status == "pass" for r in self.results)
        fails = sum(r.status == "fail" for r in self.results)
        skips = sum(r.status == "skip" for r in self.results)
        out = [
            "",
            "=" * 70,
            f" CONVERSION MATRIX: {passes} passed, {fails} failed, {skips} skipped",
            "=" * 70,
        ]
        if fails:
            out.append(" FAILED PAIRS:")
            for r in self.results:
                if r.status == "fail":
                    out.append(f"   ✗ {r.category:11} {r.in_fmt:7} → {r.out_fmt:7} {r.detail}")
        if skips:
            skipped = [r for r in self.results if r.status == "skip"]
            # Collapse skips to unique (category, in_fmt) — they repeat per out_fmt.
            seen = []
            for r in skipped:
                key = (r.category, r.in_fmt)
                if key not in [(s.category, s.in_fmt) for s in seen]:
                    seen.append(r)
            out.append(" SKIPPED INPUTS (no sample synthesizable on this machine):")
            for r in seen:
                out.append(f"   · {r.category:11} {r.in_fmt:7} {r.detail}")
        out.append("=" * 70)
        return "\n".join(out)


@pytest.fixture(scope="session")
def recorder(request) -> Recorder:
    rec = Recorder()
    request.config._matrix_recorder = rec  # stashed for terminal summary
    yield rec
    here = Path(__file__).parent
    (here / "conversion-matrix.md").write_text(rec.markdown(), encoding="utf-8")
    import json

    (here / "conversion-matrix.json").write_text(
        json.dumps(
            [
                {
                    "category": r.category,
                    "in": r.in_fmt,
                    "out": r.out_fmt,
                    "status": r.status,
                    "detail": r.detail,
                }
                for r in rec.results
            ],
            indent=1,
        ),
        encoding="utf-8",
    )


@pytest.fixture(scope="session")
def sample_cache_dir():
    d = Path(tempfile.mkdtemp(prefix="matrix_samples_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def build_matrix_params():
    """Enumerate every declared (category, in_fmt, out_fmt) pair (in != out)."""
    params = []

    async def _collect():
        for category, cls in CONVERTERS.items():
            fmts = await cls().get_supported_formats()
            ins = sorted(set(fmts["input"]))
            outs = sorted(set(fmts["output"]))
            for i in ins:
                for o in outs:
                    if i != o:
                        params.append((category, i, o))

    asyncio.run(_collect())
    return params


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    rec = getattr(config, "_matrix_recorder", None)
    if rec is not None and rec.results:
        for line in rec.console_summary().splitlines():
            terminalreporter.write_line(line)
        terminalreporter.write_line(
            f"Full grid written to {Path(__file__).parent / 'conversion-matrix.md'}"
        )
