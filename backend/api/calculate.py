"""Calculation and Excel generation endpoints."""

import os
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask
from backend.core.engine import allocate_costs
from backend.core.excel_export import generate_excel
from backend.core.statement_export import generate_statement
from backend.core.statement_pdf import generate_statement_pdf
from backend.core.data_manager import load_companies, load_settings
from backend.core.history import save_or_replace_run, find_run_for_month, get_excel_path, list_runs
from backend.core.translations import month_name
from backend.core.safe_filename import safe_name

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
    consumables_total: float = 0
    drinking_water_total: float = 0
    printer_total: float = 0
    internet_total: float = 0


class CalculateRequest(BaseModel):
    month: int
    year: int
    language: str = "en"
    monthly_input: MonthlyInput


def _validate_period(month: int, year: int):
    if month < 1 or month > 12:
        raise HTTPException(400, "Month must be 1-12.")
    if year < 2020 or year > 2100:
        raise HTTPException(400, "Year must be between 2020 and 2100.")


def _run_allocation(body: CalculateRequest):
    """Shared allocation logic for preview and save."""
    _validate_period(body.month, body.year)
    if body.language not in ("en", "ro"):
        raise HTTPException(400, "Language must be 'en' or 'ro'.")

    companies = load_companies()
    settings = load_settings()
    mi = body.monthly_input.model_dump()

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
        results = allocate_costs(companies, settings["ratios"], mi, settings=settings)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not results:
        raise HTTPException(400, "No active companies found.")

    return companies, settings, mi, results


# ── Preview only (no save) ──

@router.post("")
def calculate_preview(body: CalculateRequest):
    """Calculate allocation preview — nothing saved to history."""
    companies, settings, mi, results = _run_allocation(body)
    mn = month_name(body.month, body.language)
    filename = f"Premier_BC_{body.year}_{body.month:02d}_{mn}.xlsx"
    return {
        "results": results,
        "filename": filename,
    }


# ── Save as official report ──

@router.post("/save")
def save_official(body: CalculateRequest):
    """Save calculation as official report. Replaces existing if any."""
    companies, settings, mi, results = _run_allocation(body)

    active = [c for c in companies if c["active"]]
    mn = month_name(body.month, body.language)
    filename = f"Premier_BC_{body.year}_{body.month:02d}_{mn}.xlsx"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    generate_excel(tmp_path, results, mi, settings["ratios"], active, body.language)

    entry, old_run_id = save_or_replace_run(
        body.month, body.year, body.language, mi,
        settings["ratios"], companies, results, tmp_path
    )

    try:
        os.unlink(tmp_path)
    except OSError:
        pass

    return {
        "run_id": entry["id"],
        "filename": filename,
        "replaced": old_run_id,
        "results": results,
    }


# ── Check if month has official report ──

@router.get("/check/{year}/{month}")
def check_month(year: int, month: int):
    existing = find_run_for_month(year, month)
    if existing:
        return {
            "exists": True,
            "run_id": existing["id"],
            "generated_at": existing["generated_at"],
        }
    return {"exists": False}


# ── Statement exports ──

class StatementRequest(BaseModel):
    company_id: str
    month: int
    year: int
    language: str = "en"
    monthly_input: MonthlyInput


def _get_company_result(body: StatementRequest):
    _validate_period(body.month, body.year)
    companies = load_companies()
    settings = load_settings()
    mi = body.monthly_input.model_dump()

    company = next((c for c in companies if c["id"] == body.company_id and c["active"]), None)
    if not company:
        raise HTTPException(404, f"Active company '{body.company_id}' not found.")

    try:
        results = allocate_costs(companies, settings["ratios"], mi, settings=settings)
    except ValueError as e:
        raise HTTPException(400, str(e))

    result = next((r for r in results if r["company_id"] == body.company_id), None)
    if not result:
        raise HTTPException(400, f"No allocation result for '{body.company_id}'.")

    return company, result, mi


@router.post("/statement")
def company_statement(body: StatementRequest):
    company, result, mi = _get_company_result(body)
    filename = f"Statement_{safe_name(company['name'])}_{body.year}_{body.month:02d}.xlsx"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    generate_statement(tmp_path, company, result, body.month, body.year, mi, body.language)
    return FileResponse(tmp_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename, background=BackgroundTask(os.unlink, tmp_path))


@router.post("/statement-pdf")
def company_statement_pdf(body: StatementRequest):
    company, result, mi = _get_company_result(body)
    filename = f"Statement_{safe_name(company['name'])}_{body.year}_{body.month:02d}.pdf"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    generate_statement_pdf(tmp_path, company, result, body.month, body.year, mi, body.language)
    return FileResponse(tmp_path, media_type="application/pdf",
        filename=filename, background=BackgroundTask(os.unlink, tmp_path))


# ── Agreement PDF ──

@router.get("/agreement/{company_id}")
def company_agreement(company_id: str, language: str = "en"):
    """Generate a cost sharing agreement PDF for a company."""
    from backend.core.agreement_pdf import generate_agreement_pdf
    companies = load_companies()
    settings = load_settings()
    company = next((c for c in companies if c["id"] == company_id and c["active"]), None)
    if not company:
        raise HTTPException(404, f"Active company '{company_id}' not found.")
    filename = f"Agreement_{safe_name(company['name'])}.pdf"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    generate_agreement_pdf(tmp_path, company, settings, language)
    return FileResponse(tmp_path, media_type="application/pdf",
        filename=filename, background=BackgroundTask(os.unlink, tmp_path))


# ── Excel download ──

@router.get("/{run_id}/excel")
def download_excel(run_id: str):
    runs = list_runs()
    entry = next((r for r in runs if r["id"] == run_id), None)
    if not entry:
        raise HTTPException(404, f"Run '{run_id}' not found.")
    path = get_excel_path(entry)
    if not os.path.exists(path):
        raise HTTPException(404, "Excel file not found.")
    return FileResponse(path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(path))
