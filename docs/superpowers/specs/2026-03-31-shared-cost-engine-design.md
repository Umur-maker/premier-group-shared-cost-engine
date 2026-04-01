# Premier Group Shared Cost Engine - Design Spec

## Overview

Monthly cost allocation tool for Premier Capital & Investments Group. The secretary enters 6 invoice totals + adjustments, and the system distributes costs fairly across 13 companies based on configurable sqm/headcount ratios, then generates an Excel report.

## Data Model

### Company

```
{
  "id": "premier-capital",
  "name": "Premier Capital",
  "area_m2": 59.07,
  "headcount_default": 3,
  "building": "C4",
  "floor": "first_floor",
  "has_heating": true,
  "electricity_eligible": true,
  "water_eligible": true,
  "garbage_eligible": true,
  "active": true
}
```

### Seed Data (13 Companies)

| # | Name | Building | Floor | sqm | Headcount | Has Heating |
|---|------|----------|-------|-----|-----------|-------------|
| 1 | Chepenegescu Holding | C4 | ground_floor | 43.54 | 1 | yes |
| 2 | Mikazen | C4 | ground_floor | 35.66 | 5 | yes |
| 3 | Vendor | C4 | ground_floor | 30.04 | 1 | yes |
| 4 | Balkan | C4 | ground_floor | 25.50 | 2 | yes |
| 5 | Altay | C4 | ground_floor | 18.69 | 1 | yes |
| 6 | Windoor | C4 | ground_floor | 18.69 | 1 | yes |
| 7 | Kolnberg | C4 | ground_floor | 10.00 | 1 | no |
| 8 | GBCS | C4 | first_floor | 36.21 | 3 | yes |
| 9 | Premier Capital | C4 | first_floor | 59.07 | 3 | yes |
| 10 | Premier Rise | C4 | first_floor | 28.89 | 2 | yes |
| 11 | Premier Vision | C4 | first_floor | 30.00 | 3 | yes |
| 12 | Paul George Cata | C4 | mezzanine | 10.00 | 2 | no |
| 13 | Hotel | C1 | hotel | 277.00 | 8 | yes |

Note: Meeting Room (50 sqm) exists in source data but is NOT a payer and is NOT included.

### Allocation Ratios (configurable)

| Expense Type | sqm % | headcount % |
|--------------|-------|-------------|
| Electricity | 50 | 50 |
| Gas | 80 | 20 |
| Water | 30 | 70 |
| Garbage | 30 | 70 |

### Default Settings

| Setting | Default Value |
|---------|---------------|
| Elevator cost (RON) | 400 |

## Monthly Inputs

The secretary enters these values each month:

| # | Input | Description |
|---|-------|-------------|
| 1 | Electricity total | Total electricity bill (RON) |
| 2 | Garbage total | Total garbage bill (RON) |
| 3 | Water total | Total water bill (RON) |
| 4 | Hotel gas total | Gas bill for C1/Hotel (RON) |
| 5 | Ground floor gas total | Gas bill for C4 ground floor (RON) |
| 6 | First floor gas total | Gas bill for C4 first floor (RON) |
| 7 | External water deduction | Water consumed by external owners (RON) |
| 8 | External electricity contribution | Common area contribution by external owners (RON) |

## Allocation Logic

### Electricity

1. Start with entered electricity total
2. Subtract external electricity contribution
3. Distribute remainder to all 13 active, electricity-eligible companies
4. Distribution formula: `company_share = remaining * (sqm_ratio * sqm_weight + headcount_ratio * headcount_weight)`
   - `sqm_ratio = company_m2 / total_eligible_m2`
   - `headcount_ratio = company_headcount / total_eligible_headcount`
   - Default weights: sqm_weight = 0.50, headcount_weight = 0.50
5. Elevator cost (default 400 RON) is shown as an informational sub-component in the calculation details, not added on top

### Water

1. Start with entered water total
2. Subtract external water deduction
3. Distribute remainder to all 13 active, water-eligible companies
4. Same weighted formula: default 30% sqm + 70% headcount

### Garbage

1. Distribute full garbage total to all 13 active, garbage-eligible companies
2. Same weighted formula: default 30% sqm + 70% headcount

### Gas - Hotel

1. Full hotel gas total goes to Hotel only
2. No distribution needed (single payer)

### Gas - Ground Floor

1. Distribute to ground floor companies with `has_heating = true`
2. Eligible: Chepenegescu, Mikazen, Vendor, Balkan, Altay, Windoor (NOT Kolnberg)
3. Same weighted formula: default 80% sqm + 20% headcount

### Gas - First Floor

1. Distribute to first floor companies with `has_heating = true`
2. Eligible: GBCS, Premier Capital, Premier Rise, Premier Vision (NOT Paul George Cata - mezzanine, no heating)
3. Same weighted formula: default 80% sqm + 20% headcount

## UI Structure (Streamlit)

### Page 1: Monthly Input

- Month/Year selector
- 6 invoice amount fields
- External water deduction field
- External electricity contribution field
- "Generate Excel" button
- Download link for generated file

### Page 2: Company Management

- Table of all companies (active/inactive)
- Add new company form
- Edit company (inline or modal)
- Deactivate company (soft delete)

### Page 3: Settings

- Allocation ratio sliders (sqm % / headcount % per expense type)
- Elevator cost default
- All headcount defaults (editable per company)

## Excel Output

### Sheet 1: Summary

| Company | Total Payment (RON) |
|---------|-------------------|
| Chepenegescu Holding | 1,234.56 |
| ... | ... |
| **TOTAL** | **XX,XXX.XX** |

### Sheet 2: Detailed Breakdown

| Company | Electricity | Water | Garbage | Gas (Hotel) | Gas (GF) | Gas (1F) | Total |
|---------|------------|-------|---------|-------------|----------|----------|-------|
| Chepenegescu | 450.00 | 120.00 | 80.00 | - | 584.56 | - | 1,234.56 |
| ... | | | | | | | |

### Sheet 3: Calculation Details

- Input values entered
- Allocation ratios used
- Per expense type:
  - Total eligible sqm
  - Total eligible headcount
  - Each company's sqm ratio
  - Each company's headcount ratio
  - Each company's combined weighted ratio
  - Calculated amount

## Tech Stack

- Python 3
- Streamlit (UI)
- pandas (data manipulation)
- openpyxl (Excel generation)

## Storage

- `data/companies.json` - company master data
- `data/settings.json` - allocation ratios and defaults

## File Structure

```
premier-group-shared-cost-engine/
  app.py                  # Streamlit entry point
  engine.py               # Core allocation logic
  excel_export.py         # Excel generation
  data/
    companies.json        # Company seed data + edits
    settings.json         # Ratios and defaults
  premier-group-input/    # Reference PDFs and source Excel (read-only)
```

## Implementation Order

1. Data model + seed data (JSON files)
2. Core allocation engine (engine.py)
3. Excel export (excel_export.py)
4. Streamlit UI (app.py)
