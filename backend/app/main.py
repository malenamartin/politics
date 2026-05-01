from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings

app = FastAPI(title="Monitoreo Politico API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "env": settings.app_env}


@app.get("/")
def root() -> dict:
    return {"service": "monitoreo-politico", "docs": "/docs"}
