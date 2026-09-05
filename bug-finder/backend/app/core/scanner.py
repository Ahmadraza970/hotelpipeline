from __future__ import annotations

import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.core.linters import LintFinding, lint_file
from app.core.llm import LLMConfig, SemanticBug, judge_bugs
from app.models.schemas import Bug

DATA_DIR = Path(os.getenv("BUGFINDER_DATA_DIR", "./data/projects"))


@dataclass
class Project:
    id: str
    files: dict[str, str] = field(default_factory=dict)
    bugs: list[Bug] = field(default_factory=list)
    diffs: dict[str, dict] = field(default_factory=dict)  # bug_id -> fix payload


class ProjectStore:
    _instance: ProjectStore | None = None

    def __init__(self, root: Path = DATA_DIR):
        self.root = root
        self.projects: dict[str, Project] = {}

    @classmethod
    def get(cls) -> ProjectStore:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_or_create(self, project_id: str | None) -> Project:
        if project_id and project_id in self.projects:
            return self.projects[project_id]
        pid = project_id or f"proj_{uuid.uuid4().hex[:12]}"
        proj = Project(id=pid)
        self.projects[pid] = proj
        return proj

    def get_project(self, project_id: str) -> Project | None:
        return self.projects.get(project_id)

    def find_bug(self, project_id: str, bug_id: str) -> Bug | None:
        proj = self.projects.get(project_id)
        if not proj:
            return None
        for b in proj.bugs:
            if b.id == bug_id:
                return b
        return None


def _slug(kind: str, code: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (kind + "-" + code).lower()).strip("-")


SEVERITY_MAP = {
    "error": "High",
    "warning": "Medium",
    "info": "Low",
}


def lint_to_bug(file: str, finding: LintFinding) -> Bug:
    severity = SEVERITY_MAP.get(finding.severity, "Medium")
    # Elevate parse/compile errors to Critical.
    code = finding.rule_id.upper()
    if code.startswith(("E9", "F40", "F8", "TS", "E501")) and severity == "Low":
        severity = "Info"
    if code in {"E999", "SYNTAX"} or "syntax" in finding.message.lower():
        severity = "Critical"
    snippet = _snippet_for_line(file, finding.line)
    return Bug(
        id=f"{_slug('lint', finding.rule_id)}-{uuid.uuid4().hex[:6]}",
        file=file,
        line=finding.line,
        end_line=finding.end_line,
        column=finding.column,
        severity=severity,
        confidence=95 if severity in ("Critical", "High") else 70,
        category=finding.rule_id,
        title=finding.message.splitlines()[0] if finding.message else finding.rule_id,
        description=finding.message,
        snippet=snippet,
        source="lint",
    )


def _snippet_for_line(file: str, line: int) -> str | None:
    # Snippets are filled later from content; kept as a placeholder here.
    return None


def semantic_to_bug(file: str, bug: SemanticBug, content: str) -> Bug:
    snippet = _line_snippet(content, bug.line, bug.end_line)
    try:
        sev = Severity_from_str(bug.severity)
    except ValueError:
        sev = "Medium"
    return Bug(
        id=f"{_slug('llm', bug.category)}-{uuid.uuid4().hex[:6]}",
        file=file,
        line=bug.line,
        end_line=bug.end_line,
        column=None,
        severity=sev,
        confidence=max(0, min(100, int(bug.confidence))),
        category=bug.category,
        title=bug.title,
        description=bug.description,
        snippet=snippet,
        source="llm",
    )


SEVERITIES = ["Critical", "High", "Medium", "Low", "Info"]


def Severity_from_str(s: str) -> str:
    if s in SEVERITIES:
        return s
    low = s.lower()
    if low in ("error", "critical", "fatal"):
        return "Critical"
    if low in ("warning", "warn"):
        return "High" if "sem" in low else "Medium"
    if low in ("info", "low", "suggestion"):
        return "Low"
    return "Medium"


def _line_snippet(content: str, start: int, end: int | None = None) -> str | None:
    lines = content.splitlines()
    if not lines or start < 1:
        return None
    s = max(0, start - 1)
    e = (end - 1) if (end and end >= start) else s
    e = min(e, len(lines) - 1)
    block = lines[s : e + 1]
    return "\n".join(block) if block else None


def dedupe(bugs: list[Bug]) -> list[Bug]:
    seen = set()
    out: list[Bug] = []
    for b in bugs:
        key = (b.file, b.line, b.title)
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


class Scanner:
    def __init__(self, store: ProjectStore | None = None):
        self.store = store or ProjectStore.get()

    def scan(self, files: dict[str, str], language: str | None = None) -> tuple[str, list[Bug], float]:
        start = time.time()
        project = self.store.get_or_create(None)
        project.files.update(files)

        # Stage A: linters.
        lint_bugs: list[Bug] = []
        clean_files: dict[str, str] = {}
        for name, content in files.items():
            findings = lint_file(name, content, language)
            if findings:
                for f in findings:
                    bug = lint_to_bug(name, f)
                    bug.snippet = _line_snippet(content, bug.line, bug.end_line)
                    lint_bugs.append(bug)
            else:
                clean_files[name] = content

        # Stage B: LLM semantic judge (only on lint-clean files).
        semantic_bugs: list[Bug] = []
        if LLMConfig.from_env().available and clean_files:
            judged = judge_bugs(clean_files)
            for jb in judged:
                content = clean_files[jb.file] if jb.file in clean_files else files.get(jb.file, "")
                semantic_bugs.append(semantic_to_bug(jb.file, jb, content))

        all_bugs = dedupe(lint_bugs + semantic_bugs)
        all_bugs.sort(key=lambda b: b.rank())
        project.bugs = all_bugs
        # Keep diffs map keyed by bug id; clear stale ones not in current set.
        project.diffs = {k: v for k, v in project.diffs.items() if k in {b.id for b in all_bugs}}
        elapsed_ms = round((time.time() - start) * 1000, 2)
        return project.id, all_bugs, elapsed_ms
