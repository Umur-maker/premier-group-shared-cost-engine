"""Calculation and Excel generation endpoints."""

import os
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.core.engine import allocate_costs
from backend.core.excel_export import generate_excel
from backend.core.data_manager import load_companies, load_settings
from backend.core.history import save_run, get_excel_path
from backend.core.translations import month_name

router = APIRouter(prefix="/api/calculate", tags=["calculate"])


class MonthlyInput(BaseModel):
    electricity_total: float = 0
    water_total: float = 0
    garbage_total: float = 0
    hotel_gas_total: float = 0
    ground_floor_gas_total: float = 0
    first_floor_gas_total: float = 0
    external_electricity: float = 0
    external_water: float = 0
    external_garbage: float = 0
    external_hotel_gas: float = 0
    external_gf_gas: float = 0
    external_ff_gas: float = 0


class CalculateRequest(BaseModel):
    month: int
    year: int
    language: str = "en"
    monthly_input: MonthlyInput


@router.post("")
def calculate(body: CalculateRequest):
    if body.month < 1 or body.month > 12:
        raise HTTPException(400, "Month must be 1-12.")
    if body.language not in ("en", "ro"):
        raise HTTPException(400, "Language must be 'en' or 'ro'.")

    companies = load_companies()
    settings = load_settings()
    mi = body.monthly_input.model_dump()

    # Validate externals don't exceed totals
    checks = [
        ("electricity_total", "external_electricity", "Electricity"),
        ("water_total", "external_water", "Water"),
        ("garbage_total", "external_garbage", "Garbage"),
        ("hotel_gas_total", "external_hotel_gas", "Hotel Gas"),
        ("ground_floor_gas_total", "external_gf_gas", "Ground Floor Gas"),
        ("first_floor_gas_total", "external_ff_gas", "First Floor Gas"),
    ]
    for total_key, ext_key, label in checks:
        if mi[ext_key] > mi[total_key]:
            raise HTTPException(400, f"{label}: external usage ({mi[ext_key]}) exceeds total ({mi[total_key]}).")

    try:
        results = allocate_costs(companies, settings["ratios"], mi)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not results:
        raise HTTPException(400, "No active companies found.")

    # Generate Excel
    active = [c for c in companies if c["active"]]
    mn = month_name(body.month, body.language)
    filename = f"Premier_BC_{body.year}_{body.month:02d}_{mn}.xlsx"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    generate_excel(tmp_path, results, mi, settings["ratios"], active, body.language)

    # Save to history
    entry = save_run(body.month, body.year, body.language, mi,
                     settings["ratios"], companies, results, tmp_path)

    return {
        "results": results,
        "filename": filename,
        "run_id": entry["id"],
    }


@router.get("/{run_id}/excel")
def download_excel(run_id: str):
    from backend.core.history import list_runs
    runs = list_runs()
    entry = next((r for r in runs if r["id"] == run_id), None)
    if not entry:
        raise HTTPException(404, f"Run '{run_id}' not found.")
    path = get_excel_path(entry)
    if not os.path.exists(path):
        raise HTTPException(404, "Excel file not found.")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(path),
    )
