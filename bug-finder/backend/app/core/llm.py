from __future__ import annotations

import json
import os
from dataclasses import dataclass

DEFAULT_MODEL = "gpt-4o-mini"
JUDGE_TIMEOUT = 60
FIX_TIMEOUT = 60


@dataclass
class LLMConfig:
    api_key: str | None
    base_url: str | None
    model: str
    available: bool

    @classmethod
    def from_env(cls) -> LLMConfig:
        key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        base = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
        return cls(api_key=key, base_url=base, model=model, available=bool(key))


@dataclass
class SemanticBug:
    file: str
    line: int
    end_line: int | None
    severity: str
    confidence: int
    category: str
    title: str
    description: str
    snippet: str | None = None


_client_singleton: object | None = None


def _client():
    global _client_singleton
    if _client_singleton is not None:
        return _client_singleton
    try:
        from openai import OpenAI
    except ImportError:
        return None
    cfg = LLMConfig.from_env()
    if not cfg.available:
        return None
    kwargs = {"api_key": cfg.api_key}
    if cfg.base_url:
        kwargs["base_url"] = cfg.base_url
    _client_singleton = OpenAI(**kwargs)
    return _client_singleton


def _chat(messages: list, model: str, timeout: int) -> str | None:
    client = _client()
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=model, messages=messages, timeout=timeout, temperature=0.2
        )
        return resp.choices[0].message.content
    except Exception as exc:  # noqa: BLE001
        print(f"[llm] call failed: {exc}")
        return None


JUDGE_PROMPT = """You are a careful code reviewer. Inspect the following files and return ONLY a JSON array of real bugs that static linters typically miss: logic errors, edge cases, null/undefined dereferences, off-by-one, resource leaks, security smells, race conditions. Do NOT include style or formatting issues. Each entry: {"file","line","end_line","severity","confidence","category","title","description","snippet"}. If none, return []."""


def judge_bugs(files: dict[str, str]) -> list[SemanticBug]:
    """LLM semantic scan. Returns [] when no key configured."""
    client = _client()
    if client is None:
        return []
    cfg = LLMConfig.from_env()
    # Keep context small: only send file headers + content (cap per file).
    payload_parts = []
    for name, content in files.items():
        capped = content if len(content) <= 4000 else content[:4000]
        payload_parts.append(f"--- FILE: {name} ---\n{capped}")
    body = "\n\n".join(payload_parts)
    if not body.strip():
        return []
    text = _chat(
        [
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user", "content": body},
        ],
        model=cfg.model,
        timeout=JUDGE_TIMEOUT,
    )
    if not text:
        return []
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        raw = json.loads(text[start : end + 1]) if start != -1 and end != -1 else []
    bugs: list[SemanticBug] = []
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict):
            continue
        bugs.append(
            SemanticBug(
                file=item.get("file", ""),
                line=int(item.get("line", 1)),
                end_line=item.get("end_line"),
                severity=item.get("severity", "Medium"),
                confidence=int(item.get("confidence", 70)),
                category=item.get("category", "semantic"),
                title=item.get("title", "Possible bug"),
                description=item.get("description", ""),
                snippet=item.get("snippet"),
            )
        )
    return bugs


FIX_PROMPT = """You are a precise code autofixer. Given a reported bug, output ONLY a unified diff that fixes the bug, with no surrounding explanation, no markdown fences, no preamble. Use the exact file name from the bug context. If no safe fix is possible, output exactly: NOT_FIXABLE."""


def generate_diff(file: str, content: str, bug_description: str) -> tuple[str, bool]:
    """Return (diff_text, ok). ok=False means NOT_FIXABLE."""
    client = _client()
    if client is None:
        return "", False
    cfg = LLMConfig.from_env()
    prompt = (
        f"File: {file}\n"
        f"Bug:\n{bug_description}\n\n"
        f"Current content of the relevant region:\n{content}\n\n"
        "Return a unified diff fix (--- a/path / +++ b/path) only."
    )
    text = _chat(
        [
            {"role": "system", "content": FIX_PROMPT},
            {"role": "user", "content": prompt},
        ],
        model=cfg.model,
        timeout=FIX_TIMEOUT,
    )
    if not text:
        return "", False
    if text.strip().upper().startswith("NOT_FIXABLE"):
        return "", False
    # Only accept text that looks like a unified diff.
    if "--- " not in text or "+++ " not in text:
        return "", False
    return text.strip(), True
