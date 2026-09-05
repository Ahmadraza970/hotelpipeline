from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Severity = Literal["Critical", "High", "Medium", "Low", "Info"]
BugSource = Literal["lint", "llm"]
BugStatus = Literal["open", "dismissed", "fixed"]


class SeverityEnum(str, Enum):
    Critical = "Critical"
    High = "High"
    Medium = "Medium"
    Low = "Low"
    Info = "Info"


SEVERITY_RANK = {
    SeverityEnum.Critical: 0,
    SeverityEnum.High: 1,
    SeverityEnum.Medium: 2,
    SeverityEnum.Low: 3,
    SeverityEnum.Info: 4,
}


class Bug(BaseModel):
    id: str
    file: str
    line: int
    end_line: int | None = None
    column: int | None = None
    severity: Severity
    confidence: int = Field(ge=0, le=100)
    category: str
    title: str
    description: str
    snippet: str | None = None
    status: BugStatus = "open"
    source: BugSource

    def rank(self) -> tuple[int, int, str]:
        return (SEVERITY_RANK[SeverityEnum(self.severity)], -self.confidence, self.file)


class ScanRequest(BaseModel):
    project_id: str | None = None
    files: dict[str, str] | None = None
    repo_url: str | None = None
    language: str | None = None

    @field_validator("files")
    @classmethod
    def files_non_empty(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("files, if provided, must not be empty")
        return v


class ScanSummary(BaseModel):
    total: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_source: dict[str, int] = Field(default_factory=dict)
    languages: list[str] = Field(default_factory=list)


class ScanResult(BaseModel):
    project_id: str
    bugs: list[Bug]
    summary: ScanSummary
    elapsed_ms: float


class FixRequest(BaseModel):
    project_id: str
    bug_id: str


class FixResult(BaseModel):
    bug_id: str
    file: str
    diff: str
    lint_ok: bool
    explanation: str = ""


class ExportRequest(BaseModel):
    project_id: str | None = None
    diffs: list[FixResult] = Field(default_factory=list)
