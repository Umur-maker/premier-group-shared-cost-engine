# Workflow Redesign — Calculate → Review → Save → Pay

## Problem Statement

The current system has critical workflow issues:
1. "Generate Report" saves to history immediately — no review step
2. Same month can be calculated multiple times, creating orphaned history entries
3. Payments are keyed by (year, month), not linked to specific calculations
4. Single payment record per company — no support for multiple/partial payments
5. Overpayments are not tracked or carried forward
6. No confirmation step before saving payments

## Design Goals

- Secretary can preview before committing
- One official calculation per month
- Multiple payments per company per month with audit trail
- Overpayments carry forward as credit
- Consistent UX: enter → review → confirm → save

---

## 1. Monthly Calculation Flow

### Current (broken)
```
Enter invoices → [Generate Report] → saved to history + preview + payments
```

### New
```
Enter invoices → [Calculate Preview] → review in tabs
                                      → [Save as Official Report] → saved to history
```

### Rules
- "Calculate Preview" runs the allocation engine and shows results — nothing persisted
- Secretary can recalculate as many times as needed (changes inputs, clicks preview again)
- "Save as Official Report" commits to history with full snapshot
- Only ONE official report per month allowed
- If month already has an official report, show warning: "April 2026 already has a saved report. Replace it?"
- Replacing deletes the old run and creates a new one (payments are preserved if run_id changes — see payment linking below)

### API Changes
- `POST /api/calculate` → returns results only, does NOT save to history
- `POST /api/calculate/save` → new endpoint, saves results to history, returns run_id
- Or: add `save: boolean` flag to existing endpoint (default false)

---

## 2. Payment Ledger System

### Current (broken)
```json
{
  "2026_04": {
    "balkan": { "paid": true, "paid_amount": 1000, "paid_date": "2026-04-10" }
  }
}
```
- Single record per company per month
- Overwrites on every update
- No audit trail
- No multiple payments
- No overpayment tracking

### New: Payment Ledger
```json
{
  "entries": [
    {
      "id": "pay_001",
      "run_id": "2026_04_20260401_091234",
      "company_id": "balkan",
      "amount": 500.00,
      "date": "2026-04-10",
      "note": "bank transfer",
      "created_at": "2026-04-10T14:30:00"
    },
    {
      "id": "pay_002",
      "run_id": "2026_04_20260401_091234",
      "company_id": "balkan",
      "amount": 442.81,
      "date": "2026-04-22",
      "note": "cash",
      "created_at": "2026-04-22T09:15:00"
    }
  ]
}
```

### Payment Rules
- Each payment is an individual entry with unique ID
- Linked to a specific run_id (not just month)
- Multiple payments per company per run allowed
- Each entry has date and optional note
- Individual entries can be deleted (with confirmation)
- No editing — delete wrong entry and add correct one

### Balance Calculation
```
For a given company for a given run:
  amount_due = result.total (from frozen snapshot)
  total_paid = sum of all payment entries for this run + company
  balance = amount_due - total_paid

  if balance > 0: company owes this amount
  if balance < 0: company has credit (abs(balance) carries forward)
  if balance == 0: fully paid
```

### Carry-Forward Logic
```
For a given company up to month M:
  Walk all official runs from oldest to M:
    For each run:
      due = run result total for this company
      paid = sum of payments for this run + company
      running_balance += (due - paid)

  Final running_balance:
    > 0: total outstanding debt
    < 0: total credit available
    = 0: fully settled
```

Credit from overpayment in March automatically reduces April's effective balance.

---

## 3. Payment Tracking UI

### Location: Separate section after saved report, or dedicated payments page

### Flow
```
[Select saved month] → see companies + amounts due + payment history
  → [+ Add Payment] per company
  → enter amount, date, note
  → [Review Payments] → see summary of changes
  → [Confirm & Save] → persisted
```

### Per-Company Payment Card
```
Balkan — Due: 937,81 RON | Previous Balance: 100,00 RON | Total Due: 1.037,81 RON
┌──────────────────────────────────────────────────┐
│ 10.04.2026   500,00 RON   bank transfer       ✕ │
│ 22.04.2026   442,81 RON   cash                ✕ │
├──────────────────────────────────────────────────┤
│ Total Paid: 942,81 RON                           │
│ Balance: 95,00 RON (outstanding)                 │
└──────────────────────────────────────────────────┘
[+ Add Payment]
```

### Confirmation Dialog (before saving)
Shows:
- Number of new payments being added
- Total amount being recorded
- Companies with remaining balances
- Companies with overpayments/credits
- "Confirm & Save" / "Back to Edit"

---

## 4. History Changes

### One Official Report Per Month
- History shows one entry per month (not multiple calculations)
- If secretary recalculates, old entry is replaced
- Payment ledger entries linked to run_id are preserved or migrated

### History Entry Structure (unchanged, but enforced as unique per month)
```json
{
  "id": "2026_04_20260401_091234",
  "month": 4,
  "year": 2026,
  "language": "en",
  "generated_at": "...",
  "excel_file": "...",
  "monthly_input": {...},
  "ratios": {...},
  "company_count": 13,
  "results": [...],
  "companies": [...]
}
```

---

## 5. Manager View Changes

### Reads from:
- Official saved runs (one per month)
- Payment ledger (all entries for that run)
- Calculated balances (running balance across months)

### Shows:
- Total billed (from run results)
- Total paid (sum of all payment entries)
- Total outstanding (running balance)
- Per-company breakdown with payment history
- Credit amounts highlighted

### No toggle button — manager reviews only, does not edit payments
(Secretary handles payments, manager reviews)

---

## 6. Reports Changes

### Multi-month aggregation (unchanged logic)
- Pulls from official runs (one per month)
- Aggregates by company across selected period
- Shows totals per expense category

### New addition: Payment status per period
- For selected period, show:
  - Total billed across months
  - Total paid across months
  - Total outstanding
  - Per-company payment summary

---

## 7. API Changes Summary

| Endpoint | Change |
|----------|--------|
| `POST /api/calculate` | No longer saves to history — preview only |
| `POST /api/calculate/save` | New — saves to history (one per month) |
| `GET /api/payments/{run_id}` | Returns payment entries for a run |
| `POST /api/payments/{run_id}` | Add a payment entry |
| `DELETE /api/payments/{entry_id}` | Delete a payment entry |
| `GET /api/payments/balance/{company_id}` | Running balance for company |
| `GET /api/payments/balances/{year}/{month}` | All balances up to month |
| Old `PUT /api/payments/{year}/{month}` | Deprecated — replaced by ledger |

---

## 8. Data Migration

### From old payments.json to new ledger:
- Each old `{ "paid": true, "paid_amount": X }` becomes one ledger entry
- Linked to the latest run_id for that month
- Preserves paid_date

### From multiple history entries per month:
- Keep only the latest run per month
- Delete older duplicates
- Preserve their Excel files if needed

---

## 9. Files Affected

| File | Change |
|------|--------|
| `backend/core/payments.py` | Rewrite — ledger model |
| `backend/api/payments.py` | Rewrite — new endpoints |
| `backend/api/calculate.py` | Split into preview + save |
| `backend/core/history.py` | Add one-per-month enforcement |
| `frontend/src/app/page.tsx` | Two-step: preview then save |
| `frontend/src/app/manager/page.tsx` | Read-only, shows ledger |
| `frontend/src/app/reports/page.tsx` | Add payment summary |
| `frontend/src/types/index.ts` | New payment entry types |
| `frontend/src/lib/api.ts` | New API functions |

---

## 10. What Does NOT Change

- Allocation engine (engine.py) — zero changes
- Excel/PDF export logic
- Company management
- Settings / ratios
- Translations system
- Cost category eligibility rules
