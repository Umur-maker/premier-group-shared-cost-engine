"""History endpoints."""

import os
import tempfile
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from backend.core.history import list_runs, get_excel_path, delete_run
from backend.core.statement_pdf import generate_statement_pdf

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
    filename = f"Statement_{company['name'].replace(' ', '_')}_{entry['year']}_{entry['month']:02d}.pdf"
    tmp_path = os.path.join(tempfile.gettempdir(), filename)

    generate_statement_pdf(
        tmp_path, company, result,
        entry["month"], entry["year"],
        entry.get("monthly_input", {}), lang,
    )

    return FileResponse(tmp_path, media_type="application/pdf",
        filename=filename, background=BackgroundTask(os.unlink, tmp_path))
