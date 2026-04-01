import os
import tempfile
import openpyxl
import pytest
from excel_export import generate_excel


@pytest.fixture
def allocation_results():
    return [
        {"company_id": "comp-a", "company_name": "Company A",
         "electricity": 100.0, "water": 50.0, "garbage": 30.0,
         "gas_hotel": 0.0, "gas_ground_floor": 80.0, "gas_first_floor": 0.0, "total": 260.0},
        {"company_id": "comp-b", "company_name": "Company B",
         "electricity": 200.0, "water": 100.0, "garbage": 60.0,
         "gas_hotel": 0.0, "gas_ground_floor": 0.0, "gas_first_floor": 120.0, "total": 480.0},
        {"company_id": "hotel", "company_name": "Hotel",
         "electricity": 300.0, "water": 150.0, "garbage": 90.0,
         "gas_hotel": 500.0, "gas_ground_floor": 0.0, "gas_first_floor": 0.0, "total": 1040.0},
    ]


@pytest.fixture
def monthly_input():
    return {
        "electricity_total": 600.0,
        "garbage_total": 180.0,
        "water_total": 400.0,
        "hotel_gas_total": 500.0,
        "ground_floor_gas_total": 80.0,
        "first_floor_gas_total": 120.0,
        "external_water_deduction": 100.0,
        "external_electricity_contribution": 0.0,
    }


@pytest.fixture
def ratios():
    return {
        "electricity": {"sqm_weight": 50, "headcount_weight": 50},
        "gas": {"sqm_weight": 80, "headcount_weight": 20},
        "water": {"sqm_weight": 30, "headcount_weight": 70},
        "garbage": {"sqm_weight": 30, "headcount_weight": 70},
    }


@pytest.fixture
def companies():
    return [
        {"id": "comp-a", "name": "Company A", "area_m2": 50.0, "headcount_default": 2,
         "floor": "ground_floor", "has_heating": True, "active": True,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "building": "C4"},
        {"id": "comp-b", "name": "Company B", "area_m2": 60.0, "headcount_default": 3,
         "floor": "first_floor", "has_heating": True, "active": True,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "building": "C4"},
        {"id": "hotel", "name": "Hotel", "area_m2": 200.0, "headcount_default": 8,
         "floor": "hotel", "has_heating": True, "active": True,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "building": "C1"},
    ]


def _generate(allocation_results, monthly_input, ratios, companies):
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    generate_excel(path, allocation_results, monthly_input, ratios, companies)
    return path


def test_generate_excel_creates_file(allocation_results, monthly_input, ratios, companies):
    path = _generate(allocation_results, monthly_input, ratios, companies)
    try:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
    finally:
        os.unlink(path)


def test_excel_has_three_sheets(allocation_results, monthly_input, ratios, companies):
    path = _generate(allocation_results, monthly_input, ratios, companies)
    try:
        wb = openpyxl.load_workbook(path)
        assert wb.sheetnames == ["Summary", "Detailed Breakdown", "Calculation Details"]
    finally:
        os.unlink(path)


def test_summary_sheet_data(allocation_results, monthly_input, ratios, companies):
    path = _generate(allocation_results, monthly_input, ratios, companies)
    try:
        wb = openpyxl.load_workbook(path)
        ws = wb["Summary"]
        assert ws.cell(row=2, column=1).value == "Company A"
        assert ws.cell(row=2, column=2).value == 260.0
        assert ws.cell(row=4, column=1).value == "Hotel"
        assert ws.cell(row=4, column=2).value == 1040.0
        assert ws.cell(row=5, column=1).value == "TOTAL"
        assert ws.cell(row=5, column=2).value == 1780.0
    finally:
        os.unlink(path)


def test_detailed_sheet_headers(allocation_results, monthly_input, ratios, companies):
    path = _generate(allocation_results, monthly_input, ratios, companies)
    try:
        wb = openpyxl.load_workbook(path)
        ws = wb["Detailed Breakdown"]
        headers = [ws.cell(row=1, column=c).value for c in range(1, 9)]
        assert headers == ["Company", "Electricity", "Water", "Garbage",
                           "Gas (Hotel)", "Gas (Ground Floor)", "Gas (First Floor)", "Total"]
    finally:
        os.unlink(path)


def test_calculation_sheet_has_input_values(allocation_results, monthly_input, ratios, companies):
    path = _generate(allocation_results, monthly_input, ratios, companies)
    try:
        wb = openpyxl.load_workbook(path)
        ws = wb["Calculation Details"]
        assert ws.cell(row=1, column=1).value == "INPUT VALUES"
        # Elevator cost should NOT appear
        values = [ws.cell(row=r, column=1).value for r in range(1, 40)]
        assert not any("Elevator" in str(v) for v in values if v)
    finally:
        os.unlink(path)


def test_calculation_sheet_shows_eligible_groups(allocation_results, monthly_input, ratios, companies):
    path = _generate(allocation_results, monthly_input, ratios, companies)
    try:
        wb = openpyxl.load_workbook(path)
        ws = wb["Calculation Details"]
        values = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
        assert "ELIGIBLE COMPANIES PER EXPENSE TYPE" in values
        assert "Electricity" in values
        assert "Gas - Hotel" in values
    finally:
        os.unlink(path)
