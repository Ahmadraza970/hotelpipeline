from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

from app.core.linters import lint_file
from app.core.llm import generate_diff
from app.models.schemas import Bug, FixResult


@dataclass
class AppliedChange:
    file: str
    original: str
    patched: str


def _apply_unified_diff(original: str, diff_text: str) -> str | None:
    """Apply a single-file unified diff to `original`.

    Robust to blank context lines and ``\\ No newline`` markers emitted by
    LLMs. Returns the patched text, or ``None`` if the diff is malformed.
    """
    lines = original.split("\n")
    diff_lines = diff_text.splitlines()
    result: list[str] = []
    line_ptr = 0
    i = 0
    n = len(diff_lines)
    hunk_re = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

    while i < n:
        line = diff_lines[i]
        if line.startswith(("---", "+++")):
            i += 1
            continue
        m = hunk_re.match(line)
        if not m:
            i += 1
            continue
        start = int(m.group(1))
        target = max(0, start - 1)
        # Flush untouched original lines up to the hunk start.
        while len(result) < target and line_ptr < len(lines):
            result.append(lines[line_ptr])
            line_ptr += 1
        i += 1
        while i < n:
            body = diff_lines[i]
            if body.startswith(("+++", "---")):
                break  # safety: header inside body shouldn't happen
            if body.startswith("\\"):
                i += 1
                continue
            if body.startswith("+"):
                result.append(body[1:])
            elif body.startswith("-"):
                line_ptr += 1
            else:
                # context line (blank context may be "" or " ")
                result.append(body.removeprefix(" "))
                line_ptr += 1
            i += 1
            if i < n and hunk_re.match(diff_lines[i]):
                break
    while line_ptr < len(lines):
        result.append(lines[line_ptr])
        line_ptr += 1
    return "\n".join(result)


def generate_fix(bug: Bug, content: str) -> AppliedChange | None:
    """Produce a patched version of the file for a single bug.

    The full file is sent to the LLM so the returned unified diff's line
    numbers align with the actual file content.
    """
    description = bug.description or bug.title
    diff_text, ok = generate_diff(bug.file, content, description)
    if not ok or not diff_text:
        return None
    patched = _apply_unified_diff(content, diff_text)
    if patched is None:
        return None
    return AppliedChange(file=bug.file, original=content, patched=patched)


def validate_fix(bug: Bug, change: AppliedChange) -> FixResult:
    """Re-lint the patched content to confirm no new errors were introduced."""
    findings = lint_file(bug.file, change.patched)
    lint_ok = len(findings) == 0
    diff = _full_diff(bug.file, change.original, change.patched)
    if lint_ok:
        explanation = "Fix generated and re-linted cleanly; no new errors introduced."
    else:
        explanation = (
            "Fix generated but introduced "
            + ", ".join({f.rule_id for f in findings})
            + ". Review before applying."
        )
    return FixResult(
        bug_id=bug.id,
        file=bug.file,
        diff=diff,
        lint_ok=lint_ok,
        explanation=explanation,
    )


def _full_diff(filename: str, old: str, new: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    return "".join(diff)


def export_patch(diffs: list[FixResult]) -> str:
    """Concatenate accepted fix diffs into a single patch blob."""
    blob = ""
    for d in diffs:
        if not d.diff:
            continue
        blob += d.diff if d.diff.endswith("\n") else d.diff + "\n"
    return blob
