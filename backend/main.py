"""FastAPI entry point for Premier Business Center Shared Cost Engine."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.companies import router as companies_router
from backend.api.settings import router as settings_router
from backend.api.calculate import router as calculate_router
from backend.api.history import router as history_router
from backend.api.payments import router as payments_router

from contextlib import asynccontextmanager
from backend.core.config import ensure_data_dir


@asynccontextmanager
async def lifespan(application: FastAPI):
    ensure_data_dir()
    yield

app = FastAPI(
    title="Premier Business Center - Shared Cost Engine",
    version="3.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies_router)
app.include_router(settings_router)
app.include_router(calculate_router)
app.include_router(history_router)
app.include_router(payments_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/translations/{lang}")
def get_translations(lang: str):
    from backend.core.translations import TRANSLATIONS, MONTH_NAMES
    if lang not in TRANSLATIONS:
        lang = "en"
    return {"translations": TRANSLATIONS[lang], "months": MONTH_NAMES[lang]}


@app.get("/api/backup")
def data_backup():
    """Export all data as a single JSON for backup."""
    import json
    import tempfile
    import os
    from datetime import datetime
    from fastapi.responses import FileResponse
    from starlette.background import BackgroundTask
    from backend.core.data_manager import load_companies, load_settings
    from backend.core.history import list_runs
    from backend.core.payments import _load as _load_payments

    backup = {
        "exported_at": datetime.now().isoformat(),
        "companies": load_companies(),
        "settings": load_settings(),
        "history": list_runs(),
        "payments": _load_payments(),
    }
    filename = f"premier_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2, ensure_ascii=False)
    return FileResponse(tmp_path, media_type="application/json",
        filename=filename, background=BackgroundTask(os.unlink, tmp_path))
