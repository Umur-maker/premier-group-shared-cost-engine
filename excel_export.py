import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(bold=True, size=11, color="FFFFFF")
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)


def _style_header(ws, row, col_count):
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = THIN_BORDER


def _write_cell(ws, row, col, value, is_currency=False, bold=False):
    cell = ws.cell(row=row, column=col, value=value)
    cell.border = THIN_BORDER
    if is_currency:
        cell.number_format = "#,##0.00"
        cell.alignment = Alignment(horizontal="right")
    if bold:
        cell.font = Font(bold=True)
    return cell


def _write_summary_sheet(wb, results):
    ws = wb.create_sheet("Summary")
    headers = ["Company", "Total Payment (RON)"]
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    _style_header(ws, 1, len(headers))

    for i, r in enumerate(results, 2):
        _write_cell(ws, i, 1, r["company_name"])
        _write_cell(ws, i, 2, r["total"], is_currency=True)

    total_row = len(results) + 2
    _write_cell(ws, total_row, 1, "TOTAL", bold=True)
    _write_cell(ws, total_row, 2, round(sum(r["total"] for r in results), 2), is_currency=True, bold=True)

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 22


def _write_detailed_sheet(wb, results):
    ws = wb.create_sheet("Detailed Breakdown")
    headers = ["Company", "Electricity", "Water", "Garbage",
               "Gas (Hotel)", "Gas (Ground Floor)", "Gas (First Floor)", "Total"]
    for col, h in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=h)
    _style_header(ws, 1, len(headers))

    keys = ["electricity", "water", "garbage",
            "gas_hotel", "gas_ground_floor", "gas_first_floor", "total"]

    for i, r in enumerate(results, 2):
        _write_cell(ws, i, 1, r["company_name"])
        for j, key in enumerate(keys, 2):
            _write_cell(ws, i, j, r[key], is_currency=True)

    total_row = len(results) + 2
    _write_cell(ws, total_row, 1, "TOTAL", bold=True)
    for j, key in enumerate(keys, 2):
        _write_cell(ws, total_row, j, round(sum(r[key] for r in results), 2), is_currency=True, bold=True)

    ws.column_dimensions["A"].width = 25
    for col in range(2, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18


def _write_calculation_sheet(wb, results, monthly_input, ratios, companies, defaults):
    ws = wb.create_sheet("Calculation Details")
    row = 1

    # Section 1: Input Values
    ws.cell(row=row, column=1, value="INPUT VALUES").font = Font(bold=True, size=12)
    row += 1
    inputs = [
        ("Electricity Total (RON)", monthly_input["electricity_total"]),
        ("Garbage Total (RON)", monthly_input["garbage_total"]),
        ("Water Total (RON)", monthly_input["water_total"]),
        ("Hotel Gas Total (RON)", monthly_input["hotel_gas_total"]),
        ("Ground Floor Gas Total (RON)", monthly_input["ground_floor_gas_total"]),
        ("First Floor Gas Total (RON)", monthly_input["first_floor_gas_total"]),
        ("External Water Deduction (RON)", monthly_input.get("external_water_deduction", 0)),
        ("External Electricity Contribution (RON)", monthly_input.get("external_electricity_contribution", 0)),
        ("Elevator Cost - informational (RON)", defaults.get("elevator_cost", 400)),
    ]
    for label, value in inputs:
        ws.cell(row=row, column=1, value=label)
        c = ws.cell(row=row, column=2, value=value)
        c.number_format = "#,##0.00"
        row += 1

    row += 1

    # Section 2: Net Allocable Amounts
    ws.cell(row=row, column=1, value="NET ALLOCABLE AMOUNTS").font = Font(bold=True, size=12)
    row += 1
    net_amounts = [
        ("Electricity (after external deduction)", monthly_input["electricity_total"] - monthly_input.get("external_electricity_contribution", 0)),
        ("Water (after external deduction)", monthly_input["water_total"] - monthly_input.get("external_water_deduction", 0)),
        ("Garbage", monthly_input["garbage_total"]),
        ("Hotel Gas", monthly_input["hotel_gas_total"]),
        ("Ground Floor Gas", monthly_input["ground_floor_gas_total"]),
        ("First Floor Gas", monthly_input["first_floor_gas_total"]),
    ]
    for label, value in net_amounts:
        ws.cell(row=row, column=1, value=label)
        c = ws.cell(row=row, column=2, value=round(value, 2))
        c.number_format = "#,##0.00"
        row += 1

    row += 1

    # Section 3: Allocation Ratios
    ws.cell(row=row, column=1, value="ALLOCATION RATIOS").font = Font(bold=True, size=12)
    row += 1
    for expense_type, weights in ratios.items():
        ws.cell(row=row, column=1, value=expense_type.capitalize())
        ws.cell(row=row, column=2, value=f"{weights['sqm_weight']}% sqm + {weights['headcount_weight']}% headcount")
        row += 1

    row += 1

    # Section 4: Company details
    active = [c for c in companies if c["active"]]
    ws.cell(row=row, column=1, value="COMPANY ALLOCATION DETAILS").font = Font(bold=True, size=12)
    row += 1

    headers = ["Company", "Area (m2)", "Headcount", "Floor", "Has Heating",
               "sqm % of total", "Headcount % of total"]
    for col, h in enumerate(headers, 1):
        ws.cell(row=row, column=col, value=h)
    _style_header(ws, row, len(headers))
    row += 1

    total_sqm = sum(c["area_m2"] for c in active)
    total_hc = sum(c["headcount_default"] for c in active)

    for c in active:
        ws.cell(row=row, column=1, value=c["name"])
        ws.cell(row=row, column=2, value=c["area_m2"])
        ws.cell(row=row, column=3, value=c["headcount_default"])
        ws.cell(row=row, column=4, value=c["floor"].replace("_", " ").title())
        ws.cell(row=row, column=5, value="Yes" if c["has_heating"] else "No")
        sqm_pct = c["area_m2"] / total_sqm if total_sqm else 0
        hc_pct = c["headcount_default"] / total_hc if total_hc else 0
        ws.cell(row=row, column=6, value=round(sqm_pct * 100, 2))
        ws.cell(row=row, column=6).number_format = "0.00\"%\""
        ws.cell(row=row, column=7, value=round(hc_pct * 100, 2))
        ws.cell(row=row, column=7).number_format = "0.00\"%\""
        row += 1

    # Totals
    ws.cell(row=row, column=1, value="TOTAL").font = Font(bold=True)
    ws.cell(row=row, column=2, value=total_sqm).font = Font(bold=True)
    ws.cell(row=row, column=3, value=total_hc).font = Font(bold=True)

    ws.column_dimensions["A"].width = 30
    for col in range(2, 8):
        ws.column_dimensions[get_column_letter(col)].width = 18


def generate_excel(filepath, results, monthly_input, ratios, companies, defaults):
    """Generate a 3-sheet Excel workbook with cost allocation results."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    _write_summary_sheet(wb, results)
    _write_detailed_sheet(wb, results)
    _write_calculation_sheet(wb, results, monthly_input, ratios, companies, defaults)

    wb.save(filepath)
    return filepath
