"""Payment tracking endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.core.payments import get_payment_status, set_payment, get_all_balances
from backend.core.history import list_runs

router = APIRouter(prefix="/api/payments", tags=["payments"])


class PaymentUpdate(BaseModel):
    company_id: str
    paid: bool
    paid_amount: Optional[float] = None
    paid_date: Optional[str] = ""


@router.get("/{year}/{month}")
def get_payments(year: int, month: int):
    """Get payment status for all companies for a specific month."""
    return get_payment_status(year, month)


@router.put("/{year}/{month}")
def update_payment(year: int, month: int, body: PaymentUpdate):
    """Mark a company as paid/unpaid for a specific month."""
    result = set_payment(year, month, body.company_id, body.paid,
                         body.paid_amount or 0, body.paid_date or "")
    return {"status": "updated", **result}


@router.get("/balances/{year}/{month}")
def get_balances(year: int, month: int):
    """Get outstanding balances for all companies up to a specific month."""
    runs = list_runs()
    # Get unique company IDs from all runs
    company_ids = set()
    for run in runs:
        for r in run.get("results", []):
            company_ids.add(r["company_id"])
    return get_all_balances(year, month, runs, company_ids)
