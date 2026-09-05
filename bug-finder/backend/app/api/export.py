from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.fixer import export_patch
from app.core.scanner import ProjectStore
from app.models.schemas import ExportRequest, FixResult

router = APIRouter()
_store = ProjectStore.get()


@router.post("/export")
def export(request: ExportRequest):
    """Produce a unified patch from selected diffs (or all diffs in a project)."""
    diffs: list[FixResult] = []
    if request.diffs:
        diffs = request.diffs
    elif request.project_id:
        project = _store.get_project(request.project_id)
        if project is None:
            raise HTTPException(404, f"project '{request.project_id}' not found")
        diffs = [
            FixResult(**payload) for payload in project.diffs.values()
        ]
    else:
        raise HTTPException(400, "provide 'diffs' or 'project_id'")
    patch = export_patch(diffs)
    return {"patch": patch, "bytes": len(patch.encode("utf-8"))}
