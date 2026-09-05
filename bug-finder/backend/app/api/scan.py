from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.scanner import ProjectStore, Scanner
from app.models.schemas import ScanRequest, ScanResult, ScanSummary

router = APIRouter()
_store = ProjectStore.get()
_scanner = Scanner(_store)


@router.post("/scan", response_model=ScanResult)
def scan(request: ScanRequest):
    files = request.files or {}
    if not files and not request.repo_url:
        raise HTTPException(400, "provide 'files' (object name->content) or 'repo_url'")
    if request.repo_url and not request.files:
        # NOTE: remote repo cloning is best-effort in v1; require an explicit
        # token via LLM_API_KEY-free flow. For v1, reject gracefully.
        raise HTTPException(
            501,
            "repo_url scanning is not implemented in v1. Upload files or paste code instead.",
        )
    project_id, bugs, elapsed_ms = _scanner.scan(files, request.language)
    summary = ScanSummary(
        total=len(bugs),
        by_severity=_count(lambda b: b.severity, bugs),
        by_source=_count(lambda b: b.source, bugs),
        languages=sorted({name.rsplit(".", 1)[-1] for name in files}),
    )
    return ScanResult(project_id=project_id, bugs=bugs, summary=summary, elapsed_ms=elapsed_ms)


def _count(fn, bugs):
    counts: dict[str, int] = {}
    for b in bugs:
        key = fn(b)
        counts[key] = counts.get(key, 0) + 1
    return counts
