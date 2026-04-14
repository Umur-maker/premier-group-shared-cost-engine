"""History endpoints."""

import os
import json
import shutil
import tempfile
import zipfile
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from backend.core.history import list_runs, get_excel_path, delete_run, save_or_replace_run
from backend.core.engine import allocate_costs
from backend.core.excel_export import generate_excel
from backend.core.statement_pdf import generate_statement_pdf
from backend.core.data_manager import load_companies, load_settings
from backend.core.translations import month_name
from backend.core.safe_filename import safe_name

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def get_history():
    runs = list_runs()
    # Return entries without heavy snapshots for the list view
    return [
        {k: v for k, v in entry.items() if k not in ("results", "companies")}
        for entry in runs
    ]


@router.get("/{run_id}")
def get_run_detail(run_id: str):
    """Get full run detail including results and companies snapshot."""
    runs = list_runs()
    entry = next((r for r in runs if r["id"] == run_id), None)
    if not entry:
        raise HTTPException(404, f"Run '{run_id}' not found.")
    return entry


@router.delete("/{run_id}")
def remove_run(run_id: str):
    runs = list_runs()
    if not any(r["id"] == run_id for r in runs):
        raise HTTPException(404, f"Run '{run_id}' not found.")
    delete_run(run_id)
    return {"status": "deleted", "id": run_id}


@router.get("/{run_id}/excel")
def download_history_excel(run_id: str):
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


@router.get("/{run_id}/statement-pdf")
def history_statement_pdf(run_id: str, company_id: str = Query(...)):
    """Generate a company statement PDF from a historical run snapshot."""
    runs = list_runs()
    entry = next((r for r in runs if r["id"] == run_id), None)
    if not entry:
        raise HTTPException(404, f"Run '{run_id}' not found.")

    # Use stored snapshots — not live data
    results = entry.get("results")
    companies = entry.get("companies")

    if not results or not companies:
        raise HTTPException(400,
            "This historical run does not contain snapshot data. "
            "Only runs generated after the snapshot feature was added support this.")

    company = next((c for c in companies if c["id"] == company_id), None)
    if not company:
        raise HTTPException(404, f"Company '{company_id}' not found in this run's snapshot.")

    result = next((r for r in results if r["company_id"] == company_id), None)
    if not result:
        raise HTTPException(404, f"No allocation result for '{company_id}' in this run.")

    lang = entry.get("language", "en")
    settings = load_settings()
    filename = f"Statement_{safe_name(company['name'])}_{entry['year']}_{entry['month']:02d}.pdf"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)

    generate_statement_pdf(
        tmp_path, company, result,
        entry["month"], entry["year"],
        entry.get("monthly_input", {}), lang,
        eur_rate=entry.get("ratios", {}).get("eur_ron_rate") or settings.get("eur_ron_rate"),
        sublet_info=settings.get("hotel_sublet"),
    )

    return FileResponse(tmp_path, media_type="application/pdf",
        filename=filename, background=BackgroundTask(os.unlink, tmp_path))


@router.post("/{run_id}/recalculate")
def recalculate_run(run_id: str):
    """Re-run allocation with stored monthly_input but current company data & settings."""
    runs = list_runs()
    entry = next((r for r in runs if r["id"] == run_id), None)
    if not entry:
        raise HTTPException(404, f"Run '{run_id}' not found.")

    mi = entry.get("monthly_input")
    if not mi:
        raise HTTPException(400, "This run has no stored monthly input data.")

    companies = load_companies()
    settings = load_settings()
    lang = entry.get("language", "en")

    try:
        results = allocate_costs(companies, settings["ratios"], mi, settings=settings)
    except ValueError as e:
        raise HTTPException(400, str(e))

    active = [c for c in companies if c["active"]]
    mn = month_name(entry["month"], lang)
    filename = f"Premier_BC_{entry['year']}_{entry['month']:02d}_{mn}.xlsx"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)
    mi["_eur_rate"] = settings.get("eur_ron_rate", 5.1)
    generate_excel(tmp_path, results, mi, settings["ratios"], active, lang)

    new_entry, old_id = save_or_replace_run(
        entry["month"], entry["year"], lang, mi,
        settings["ratios"], companies, results, tmp_path
    )
    try:
        os.unlink(tmp_path)
    except OSError:
        pass

    return {"run_id": new_entry["id"], "replaced": old_id, "results": results}


@router.get("/{run_id}/statements-zip")
def download_all_statements(run_id: str):
    """Generate a ZIP with PDF statements for all companies in this run."""
    runs = list_runs()
    entry = next((r for r in runs if r["id"] == run_id), None)
    if not entry:
        raise HTTPException(404, f"Run '{run_id}' not found.")

    results = entry.get("results")
    companies = entry.get("companies")
    if not results or not companies:
        raise HTTPException(400, "Snapshot data not available for this run.")

    lang = entry.get("language", "en")
    settings = load_settings()
    eur_rate = settings.get("eur_ron_rate")
    zip_filename = f"Statements_{entry['year']}_{entry['month']:02d}.zip"
    zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for result in results:
            if result.get("total", 0) <= 0:
                continue
            company = next((c for c in companies if c["id"] == result["company_id"]), None)
            if not company:
                continue
            pdf_name = f"Statement_{safe_name(company['name'])}_{entry['year']}_{entry['month']:02d}.pdf"
            pdf_path = os.path.join(tempfile.gettempdir(), pdf_name)
            generate_statement_pdf(
                pdf_path, company, result,
                entry["month"], entry["year"],
                entry.get("monthly_input", {}), lang,
                eur_rate=eur_rate,
                sublet_info=settings.get("hotel_sublet"),
            )
            zf.write(pdf_path, pdf_name)
            try:
                os.unlink(pdf_path)
            except OSError:
                pass

    return FileResponse(zip_path, media_type="application/zip",
        filename=zip_filename, background=BackgroundTask(os.unlink, zip_path))
