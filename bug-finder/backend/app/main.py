from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import export, fix, scan

app = FastAPI(
    title="Bug Finder",
    description="Find and fix bugs across any codebase via lint + LLM review.",
    version="0.1.0",
)

origins = __import__("os").getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def root():
    return {"service": "bug-finder", "version": "0.1.0", "docs": "/docs"}


app.include_router(scan.router)
app.include_router(fix.router)
app.include_router(export.router)
