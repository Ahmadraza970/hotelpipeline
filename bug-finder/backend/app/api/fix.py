from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.fixer import generate_fix, validate_fix
from app.core.llm import LLMConfig
from app.core.scanner import ProjectStore
from app.models.schemas import FixRequest, FixResult

router = APIRouter()
_store = ProjectStore.get()


@router.post("/fix", response_model=FixResult)
def fix(request: FixRequest):
    if not LLMConfig.from_env().available:
        raise HTTPException(
            503,
            "LLM provider not configured. Set LLM_API_KEY (and optionally LLM_BASE_URL/LLM_MODEL). "
            "Lint-only mode is still available via /scan.",
        )
    bug = _store.find_bug(request.project_id, request.bug_id)
    if bug is None:
        project = _store.get_project(request.project_id)
        raise HTTPException(404, f"bug '{request.bug_id}' not found in project '{request.project_id}'" if project else f"project '{request.project_id}' not found")
    content = _store.get_project(request.project_id).files.get(bug.file)
    if content is None:
        raise HTTPException(404, f"file '{bug.file}' not in project")
    applied = generate_fix(bug, content)
    if applied is None:
        raise HTTPException(422, "No fix could be generated for this bug.")
    result = validate_fix(bug, applied)
    _store.get_project(request.project_id).diffs[bug.id] = {
        "bug_id": result.bug_id,
        "file": result.file,
        "diff": result.diff,
        "lint_ok": result.lint_ok,
        "explanation": result.explanation,
    }
    return result
