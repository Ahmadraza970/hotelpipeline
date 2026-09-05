from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

LINT_TIMEOUT = 25


def _ruff_cmd() -> list[str] | None:
    """Resolve a ruff invocation: prefer the PATH binary, fall back to `python -m ruff`."""
    binary = shutil.which("ruff")
    if binary:
        return [binary]
    import importlib.util

    try:
        spec = importlib.util.find_spec("ruff")
    except (ImportError, ValueError):
        spec = None
    if spec is not None:
        return [sys.executable, "-m", "ruff"]
    return None


@dataclass
class LintFinding:
    """A raw finding emitted by a linter, pre-severity-mapping."""

    rule_id: str
    severity: str
    message: str
    line: int
    end_line: int | None = None
    column: int | None = None
    docs_url: str | None = None


def _has(cmd: str) -> str | None:
    return shutil.which(cmd)


def _run(cmd: list[str], *, input: str | None = None, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        input=input,
        capture_output=True,
        text=True,
        timeout=LINT_TIMEOUT,
        cwd=cwd,
        check=False,
    )


def _iter_ruff_checkers(node) -> list[dict]:
    """Recursively collect ruff finding dicts regardless of JSON schema version."""
    found: list[dict] = []
    if isinstance(node, dict):
        if "code" in node and ("location" in node or "end" in node or "end_location" in node):
            found.append(node)
        for v in node.values():
            found.extend(_iter_ruff_checkers(v))
    elif isinstance(node, list):
        for item in node:
            found.extend(_iter_ruff_checkers(item))
    return found


def lint_python_ruff(filename: str, content: str) -> list[LintFinding]:
    ruff_cmd = _ruff_cmd()
    if not ruff_cmd:
        return []
    try:
        proc = _run(
            ruff_cmd + ["check", "--output-format", "json", "--stdin-filename", filename, "-"],
            input=content,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    # ruff: 0 clean, 1 violations, other = error/irrelevant
    if proc.returncode not in (0, 1):
        return []
    raw = proc.stdout.strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    findings: list[LintFinding] = []
    for item in _iter_ruff_checkers(data):
        loc = item.get("location") or {}
        end = item.get("end") or item.get("end_location") or {}
        row = loc.get("row") or loc.get("line") or 1
        col = loc.get("column") or loc.get("col")
        end_line = end.get("row") or end.get("line")
        findings.append(
            LintFinding(
                rule_id=str(item.get("code", "RUFF")),
                severity=_ruff_severity(item),
                message=item.get("message") or item.get("description") or "",
                line=int(row),
                end_line=int(end_line) if end_line else None,
                column=int(col) if col else None,
                docs_url=item.get("url") or item.get("docs_url"),
            )
        )
    return findings


def _ruff_severity(item: dict) -> str:
    sev = item.get("severity", "")
    if sev == "Error":
        return "error"
    if sev == "Warning":
        return "warning"
    if sev == "Info":
        return "info"
    code = str(item.get("code", ""))
    prefix = code[0] if code else ""
    if prefix in ("F", "E9", "E"):
        return "error"
    if prefix in ("W",):
        return "warning"
    return "info"


def lint_js_eslint(filename: str, content: str) -> list[LintFinding]:
    """ESLint via temp file + JSON formatter. Handles .js and .ts with TS parser."""
    eslint = _has("npx") or _has("eslint")
    if not eslint:
        return []
    findings: list[LintFinding] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fpath = root / filename
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
        _write_eslint_config(root, filename)
        cmd = (
            [eslint, "--no-ignore", "--format", "json"]
            if eslint.endswith("eslint")
            else ["npx", "--no-install", "eslint", "--no-ignore", "--format", "json", filename]
        )
        try:
            proc = _run(cmd, cwd=str(root))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []
        if proc.returncode not in (0, 1):
            return []
        out = proc.stdout.strip()
        if not out:
            return []
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            return []
    if isinstance(data, list):
        for entry in data:
            for m in entry.get("messages", []):
                if m.get("fatal") or not m.get("ruleId"):
                    continue
                findings.append(
                    LintFinding(
                        rule_id=str(m.get("ruleId", "eslint")),
                        severity="error" if m.get("severity") == 2 else "warning",
                        message=m.get("message", ""),
                        line=int(m.get("line", 1)),
                        end_line=m.get("endLine") or None,
                        column=m.get("column"),
                        docs_url=m.get("helpUrl"),
                    )
                )
    return findings


def _write_eslint_config(root: Path, filename: str) -> str:
    """Minimal eslint config: uses TS parser/config when needed, env-friendly."""
    is_ts = filename.endswith((".ts", ".tsx"))
    config_name = "eslint.config.mjs"
    cfg = root / config_name
    if is_ts:
        content = (
            "import ts from 'typescript-eslint';\n"
            "export default ts.configs.recommended;\n"
        )
    else:
        content = (
            "import js from '@eslint/js';\n"
            "export default [js.configs.recommended];\n"
        )
    cfg.write_text(content, encoding="utf-8")
    return config_name


def typecheck_ts(filename: str, content: str) -> list[LintFinding]:
    """Best-effort tsc typecheck via temp project. Returns [] if tsc absent."""
    tsc = _has("npx")
    if not tsc:
        return []
    findings: list[LintFinding] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tsconfig.json").write_text(
            json.dumps(
                {
                    "compilerOptions": {
                        "strict": True,
                        "noEmit": True,
                        "skipLibCheck": True,
                        "module": "esnext",
                        "moduleResolution": "bundler",
                        "target": "es2022",
                        "jsx": "react",
                        "forceConsistentCasingInFileNames": True,
                    },
                    "files": [filename],
                }
            ),
            encoding="utf-8",
        )
        fpath = root / filename
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text(content, encoding="utf-8")
        try:
            proc = _run(
                ["npx", "--no-install", "tsc", "-p", "tsconfig.json", "--pretty", "false"],
                cwd=str(root),
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []
    # tsc prints "file(line,col): error TS1234: msg" lines.
    for line in proc.stdout.splitlines() + proc.stderr.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        head, _, rest = line.partition(":")
        if not head.endswith(filename):
            continue
        # parse (line,col): severity code: message
        import re

        m = re.match(r"\((\d+),(\d+)\)\s*:\s*(error|warning)\s*(TS\d+)\s*:\s*(.*)", rest)
        if not m:
            continue
        findings.append(
            LintFinding(
                rule_id=m.group(4),
                severity=m.group(3),
                message=m.group(5),
                line=int(m.group(1)),
                column=int(m.group(2)),
            )
        )
    return findings


LANGUAGES_BY_EXT: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}


def detect_language(filename: str) -> str | None:
    ext = Path(filename).suffix.lower()
    return LANGUAGES_BY_EXT.get(ext)


def lint_file(filename: str, content: str, lang: str | None = None) -> list[LintFinding]:
    language = lang or detect_language(filename) or ""
    out: list[LintFinding] = []
    if language == "python":
        out.extend(lint_python_ruff(filename, content))
    elif language in ("javascript", "typescript"):
        out.extend(lint_js_eslint(filename, content))
        if language == "typescript":
            out.extend(typecheck_ts(filename, content))
    return out
