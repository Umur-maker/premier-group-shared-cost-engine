"""FastAPI entry point for Premier Business Center Shared Cost Engine."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.companies import router as companies_router
from backend.api.settings import router as settings_router
from backend.api.calculate import router as calculate_router
from backend.api.history import router as history_router
from backend.api.payments import router as payments_router

app = FastAPI(
    title="Premier Business Center - Shared Cost Engine",
    version="2.0.0",
)

cors_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in cors_origins],
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
