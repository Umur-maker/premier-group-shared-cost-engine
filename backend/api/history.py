"""History endpoints."""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.core.history import list_runs, get_excel_path, delete_run

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def get_history():
    return list_runs()


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
