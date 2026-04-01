# Premier Group Shared Cost Engine - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit app where the secretary enters monthly invoice totals and generates an Excel report distributing costs across 13+ configurable companies.

**Architecture:** JSON files store company data and settings. A pure-function allocation engine computes cost shares. An Excel exporter produces a 3-sheet workbook. Streamlit ties it together with a simple UI.

**Tech Stack:** Python 3, Streamlit, pandas, openpyxl

---

## File Map

| File | Responsibility |
|------|---------------|
| `data/companies.json` | Company master data (seed + edits) |
| `data/settings.json` | Allocation ratios and defaults |
| `data_manager.py` | Load/save JSON files |
| `engine.py` | Pure allocation logic |
| `excel_export.py` | Generate 3-sheet Excel workbook |
| `app.py` | Streamlit UI |
| `tests/test_engine.py` | Tests for allocation engine |
| `tests/test_excel_export.py` | Tests for Excel generation |
| `requirements.txt` | Python dependencies |

---

### Task 1: Project Setup and Seed Data

**Files:**
- Create: `requirements.txt`
- Create: `data/companies.json`
- Create: `data/settings.json`
- Create: `data_manager.py`
- Create: `tests/__init__.py`
- Create: `tests/test_data_manager.py`

- [ ] **Step 1: Create requirements.txt**

```
streamlit>=1.30.0
pandas>=2.0.0
openpyxl>=3.1.0
pytest>=7.0.0
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`

- [ ] **Step 3: Create data/companies.json**

```json
[
  {
    "id": "chepenegescu-holding",
    "name": "Chepenegescu Holding",
    "area_m2": 43.54,
    "headcount_default": 1,
    "building": "C4",
    "floor": "ground_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "mikazen",
    "name": "Mikazen",
    "area_m2": 35.66,
    "headcount_default": 5,
    "building": "C4",
    "floor": "ground_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "vendor",
    "name": "Vendor",
    "area_m2": 30.04,
    "headcount_default": 1,
    "building": "C4",
    "floor": "ground_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "balkan",
    "name": "Balkan",
    "area_m2": 25.50,
    "headcount_default": 2,
    "building": "C4",
    "floor": "ground_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "altay",
    "name": "Altay",
    "area_m2": 18.69,
    "headcount_default": 1,
    "building": "C4",
    "floor": "ground_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "windoor",
    "name": "Windoor",
    "area_m2": 18.69,
    "headcount_default": 1,
    "building": "C4",
    "floor": "ground_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "kolnberg",
    "name": "Kolnberg",
    "area_m2": 10.00,
    "headcount_default": 1,
    "building": "C4",
    "floor": "ground_floor",
    "has_heating": false,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "gbcs",
    "name": "GBCS",
    "area_m2": 36.21,
    "headcount_default": 3,
    "building": "C4",
    "floor": "first_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
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
  },
  {
    "id": "premier-rise",
    "name": "Premier Rise",
    "area_m2": 28.89,
    "headcount_default": 2,
    "building": "C4",
    "floor": "first_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "premier-vision",
    "name": "Premier Vision",
    "area_m2": 30.00,
    "headcount_default": 3,
    "building": "C4",
    "floor": "first_floor",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "paul-george-cata",
    "name": "Paul George Cata",
    "area_m2": 10.00,
    "headcount_default": 2,
    "building": "C4",
    "floor": "mezzanine",
    "has_heating": false,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  },
  {
    "id": "hotel",
    "name": "Hotel",
    "area_m2": 277.00,
    "headcount_default": 8,
    "building": "C1",
    "floor": "hotel",
    "has_heating": true,
    "electricity_eligible": true,
    "water_eligible": true,
    "garbage_eligible": true,
    "active": true
  }
]
```

- [ ] **Step 4: Create data/settings.json**

```json
{
  "ratios": {
    "electricity": {"sqm_weight": 50, "headcount_weight": 50},
    "gas": {"sqm_weight": 80, "headcount_weight": 20},
    "water": {"sqm_weight": 30, "headcount_weight": 70},
    "garbage": {"sqm_weight": 30, "headcount_weight": 70}
  },
  "defaults": {
    "elevator_cost": 400
  }
}
```

- [ ] **Step 5: Create data_manager.py**

```python
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
COMPANIES_FILE = os.path.join(DATA_DIR, "companies.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def load_companies():
    with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_companies(companies):
    with open(COMPANIES_FILE, "w", encoding="utf-8") as f:
        json.dump(companies, f, indent=2, ensure_ascii=False)


def load_settings():
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def add_company(company):
    companies = load_companies()
    companies.append(company)
    save_companies(companies)
    return companies


def update_company(company_id, updated_fields):
    companies = load_companies()
    for c in companies:
        if c["id"] == company_id:
            c.update(updated_fields)
            break
    save_companies(companies)
    return companies


def deactivate_company(company_id):
    return update_company(company_id, {"active": False})


def get_active_companies():
    return [c for c in load_companies() if c["active"]]
```

- [ ] **Step 6: Write test for data_manager**

Create `tests/__init__.py` (empty file) and `tests/test_data_manager.py`:

```python
import json
import os
import tempfile
import pytest
from unittest.mock import patch
import data_manager


@pytest.fixture
def sample_companies():
    return [
        {
            "id": "company-a",
            "name": "Company A",
            "area_m2": 50.0,
            "headcount_default": 3,
            "building": "C4",
            "floor": "ground_floor",
            "has_heating": True,
            "electricity_eligible": True,
            "water_eligible": True,
            "garbage_eligible": True,
            "active": True,
        },
        {
            "id": "company-b",
            "name": "Company B",
            "area_m2": 30.0,
            "headcount_default": 2,
            "building": "C4",
            "floor": "first_floor",
            "has_heating": False,
            "electricity_eligible": True,
            "water_eligible": True,
            "garbage_eligible": True,
            "active": True,
        },
    ]


@pytest.fixture
def tmp_data_dir(sample_companies):
    with tempfile.TemporaryDirectory() as tmpdir:
        companies_file = os.path.join(tmpdir, "companies.json")
        settings_file = os.path.join(tmpdir, "settings.json")
        with open(companies_file, "w") as f:
            json.dump(sample_companies, f)
        with open(settings_file, "w") as f:
            json.dump({
                "ratios": {
                    "electricity": {"sqm_weight": 50, "headcount_weight": 50},
                    "gas": {"sqm_weight": 80, "headcount_weight": 20},
                    "water": {"sqm_weight": 30, "headcount_weight": 70},
                    "garbage": {"sqm_weight": 30, "headcount_weight": 70},
                },
                "defaults": {"elevator_cost": 400},
            }, f)
        with patch.object(data_manager, "COMPANIES_FILE", companies_file), \
             patch.object(data_manager, "SETTINGS_FILE", settings_file):
            yield tmpdir


def test_load_companies(tmp_data_dir, sample_companies):
    companies = data_manager.load_companies()
    assert len(companies) == 2
    assert companies[0]["name"] == "Company A"


def test_get_active_companies(tmp_data_dir):
    companies = data_manager.get_active_companies()
    assert len(companies) == 2


def test_deactivate_company(tmp_data_dir):
    data_manager.deactivate_company("company-b")
    active = data_manager.get_active_companies()
    assert len(active) == 1
    assert active[0]["id"] == "company-a"


def test_add_company(tmp_data_dir):
    new_company = {
        "id": "company-c",
        "name": "Company C",
        "area_m2": 20.0,
        "headcount_default": 1,
        "building": "C4",
        "floor": "ground_floor",
        "has_heating": True,
        "electricity_eligible": True,
        "water_eligible": True,
        "garbage_eligible": True,
        "active": True,
    }
    result = data_manager.add_company(new_company)
    assert len(result) == 3


def test_update_company(tmp_data_dir):
    data_manager.update_company("company-a", {"headcount_default": 5})
    companies = data_manager.load_companies()
    assert companies[0]["headcount_default"] == 5


def test_load_settings(tmp_data_dir):
    settings = data_manager.load_settings()
    assert settings["ratios"]["electricity"]["sqm_weight"] == 50
    assert settings["defaults"]["elevator_cost"] == 400
```

- [ ] **Step 7: Run tests**

Run: `pytest tests/test_data_manager.py -v`
Expected: All 6 tests PASS

- [ ] **Step 8: Commit**

```bash
git init
git add requirements.txt data/ data_manager.py tests/
git commit -m "feat: project setup with seed data and data manager"
```

---

### Task 2: Core Allocation Engine

**Files:**
- Create: `engine.py`
- Create: `tests/test_engine.py`

- [ ] **Step 1: Write failing tests for allocation engine**

Create `tests/test_engine.py`:

```python
import pytest
from engine import allocate_costs


@pytest.fixture
def companies():
    return [
        {"id": "gf-a", "name": "GF-A", "area_m2": 40.0, "headcount_default": 2,
         "building": "C4", "floor": "ground_floor", "has_heating": True,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "active": True},
        {"id": "gf-b", "name": "GF-B", "area_m2": 10.0, "headcount_default": 1,
         "building": "C4", "floor": "ground_floor", "has_heating": False,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "active": True},
        {"id": "ff-a", "name": "FF-A", "area_m2": 60.0, "headcount_default": 3,
         "building": "C4", "floor": "first_floor", "has_heating": True,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "active": True},
        {"id": "hotel", "name": "Hotel", "area_m2": 200.0, "headcount_default": 8,
         "building": "C1", "floor": "hotel", "has_heating": True,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "active": True},
    ]


@pytest.fixture
def ratios():
    return {
        "electricity": {"sqm_weight": 50, "headcount_weight": 50},
        "gas": {"sqm_weight": 80, "headcount_weight": 20},
        "water": {"sqm_weight": 30, "headcount_weight": 70},
        "garbage": {"sqm_weight": 30, "headcount_weight": 70},
    }


@pytest.fixture
def monthly_input():
    return {
        "electricity_total": 1000.0,
        "garbage_total": 400.0,
        "water_total": 500.0,
        "hotel_gas_total": 300.0,
        "ground_floor_gas_total": 200.0,
        "first_floor_gas_total": 250.0,
        "external_water_deduction": 100.0,
        "external_electricity_contribution": 50.0,
    }


@pytest.fixture
def defaults():
    return {"elevator_cost": 400}


def test_allocate_costs_returns_all_companies(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    assert len(result) == 4
    assert all("company_id" in r for r in result)
    assert all("company_name" in r for r in result)
    assert all("total" in r for r in result)


def test_allocate_costs_has_all_expense_types(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    for r in result:
        assert "electricity" in r
        assert "water" in r
        assert "garbage" in r
        assert "gas_hotel" in r
        assert "gas_ground_floor" in r
        assert "gas_first_floor" in r


def test_electricity_sums_to_total_minus_external(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    elec_sum = sum(r["electricity"] for r in result)
    expected = monthly_input["electricity_total"] - monthly_input["external_electricity_contribution"]
    assert abs(elec_sum - expected) < 0.01


def test_water_sums_to_total_minus_external(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    water_sum = sum(r["water"] for r in result)
    expected = monthly_input["water_total"] - monthly_input["external_water_deduction"]
    assert abs(water_sum - expected) < 0.01


def test_garbage_sums_to_total(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    garbage_sum = sum(r["garbage"] for r in result)
    assert abs(garbage_sum - monthly_input["garbage_total"]) < 0.01


def test_hotel_gas_only_to_hotel(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    for r in result:
        if r["company_id"] == "hotel":
            assert r["gas_hotel"] == 300.0
        else:
            assert r["gas_hotel"] == 0.0


def test_ground_floor_gas_excludes_no_heating(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    gf_b = next(r for r in result if r["company_id"] == "gf-b")
    assert gf_b["gas_ground_floor"] == 0.0
    gf_a = next(r for r in result if r["company_id"] == "gf-a")
    assert gf_a["gas_ground_floor"] == 200.0  # only eligible GF company


def test_first_floor_gas_only_to_first_floor(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    ff_a = next(r for r in result if r["company_id"] == "ff-a")
    assert ff_a["gas_first_floor"] == 250.0  # only eligible FF company
    for r in result:
        if r["company_id"] != "ff-a":
            assert r["gas_first_floor"] == 0.0


def test_total_is_sum_of_all_expenses(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    for r in result:
        expected_total = (
            r["electricity"] + r["water"] + r["garbage"]
            + r["gas_hotel"] + r["gas_ground_floor"] + r["gas_first_floor"]
        )
        assert abs(r["total"] - expected_total) < 0.01


def test_inactive_companies_excluded(companies, ratios, monthly_input, defaults):
    companies[0]["active"] = False
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    assert len(result) == 3
    assert all(r["company_id"] != "gf-a" for r in result)


def test_weighted_distribution_electricity(companies, ratios, monthly_input, defaults):
    """With 50/50 weights, verify the formula works correctly."""
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    remaining = 1000.0 - 50.0  # 950
    # total sqm: 40+10+60+200 = 310, total headcount: 2+1+3+8 = 14
    # gf-a: sqm_ratio=40/310, hc_ratio=2/14
    # share = 950 * (0.5 * 40/310 + 0.5 * 2/14)
    gf_a = next(r for r in result if r["company_id"] == "gf-a")
    expected = 950 * (0.5 * 40.0 / 310.0 + 0.5 * 2.0 / 14.0)
    assert abs(gf_a["electricity"] - expected) < 0.01
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_engine.py -v`
Expected: FAIL (engine module not found)

- [ ] **Step 3: Implement engine.py**

```python
def _distribute(amount, eligible_companies, sqm_weight, headcount_weight, headcount_overrides=None):
    """Distribute an amount across companies based on weighted sqm + headcount formula.

    Returns dict of {company_id: share}.
    """
    if not eligible_companies or amount <= 0:
        return {}

    w_sqm = sqm_weight / 100.0
    w_hc = headcount_weight / 100.0

    total_sqm = sum(c["area_m2"] for c in eligible_companies)
    overrides = headcount_overrides or {}
    total_hc = sum(overrides.get(c["id"], c["headcount_default"]) for c in eligible_companies)

    result = {}
    for c in eligible_companies:
        sqm_ratio = c["area_m2"] / total_sqm if total_sqm > 0 else 0
        hc = overrides.get(c["id"], c["headcount_default"])
        hc_ratio = hc / total_hc if total_hc > 0 else 0
        result[c["id"]] = amount * (w_sqm * sqm_ratio + w_hc * hc_ratio)

    # Fix rounding: adjust largest share so total matches exactly
    distributed = sum(result.values())
    if result and abs(distributed - amount) > 0.001:
        largest_id = max(result, key=result.get)
        result[largest_id] += amount - distributed

    return result


def allocate_costs(companies, ratios, monthly_input, defaults, headcount_overrides=None):
    """Main allocation function.

    Args:
        companies: list of company dicts
        ratios: dict with keys electricity/gas/water/garbage, each having sqm_weight/headcount_weight
        monthly_input: dict with electricity_total, garbage_total, water_total,
                       hotel_gas_total, ground_floor_gas_total, first_floor_gas_total,
                       external_water_deduction, external_electricity_contribution
        defaults: dict with elevator_cost
        headcount_overrides: optional dict of {company_id: headcount} for this month

    Returns:
        list of dicts, one per active company, with per-expense and total amounts
    """
    active = [c for c in companies if c["active"]]
    overrides = headcount_overrides or {}

    # Electricity: all eligible, subtract external contribution
    elec_eligible = [c for c in active if c["electricity_eligible"]]
    elec_amount = monthly_input["electricity_total"] - monthly_input.get("external_electricity_contribution", 0)
    elec_shares = _distribute(
        elec_amount, elec_eligible,
        ratios["electricity"]["sqm_weight"], ratios["electricity"]["headcount_weight"],
        overrides,
    )

    # Water: all eligible, subtract external deduction
    water_eligible = [c for c in active if c["water_eligible"]]
    water_amount = monthly_input["water_total"] - monthly_input.get("external_water_deduction", 0)
    water_shares = _distribute(
        water_amount, water_eligible,
        ratios["water"]["sqm_weight"], ratios["water"]["headcount_weight"],
        overrides,
    )

    # Garbage: all eligible, full amount
    garbage_eligible = [c for c in active if c["garbage_eligible"]]
    garbage_shares = _distribute(
        monthly_input["garbage_total"], garbage_eligible,
        ratios["garbage"]["sqm_weight"], ratios["garbage"]["headcount_weight"],
        overrides,
    )

    # Gas Hotel: only hotel companies
    hotel_gas_eligible = [c for c in active if c["floor"] == "hotel" and c["has_heating"]]
    hotel_gas_shares = _distribute(
        monthly_input["hotel_gas_total"], hotel_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"],
        overrides,
    )

    # Gas Ground Floor: ground floor with heating
    gf_gas_eligible = [c for c in active if c["floor"] == "ground_floor" and c["has_heating"]]
    gf_gas_shares = _distribute(
        monthly_input["ground_floor_gas_total"], gf_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"],
        overrides,
    )

    # Gas First Floor: first floor with heating
    ff_gas_eligible = [c for c in active if c["floor"] == "first_floor" and c["has_heating"]]
    ff_gas_shares = _distribute(
        monthly_input["first_floor_gas_total"], ff_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"],
        overrides,
    )

    # Build result
    results = []
    for c in active:
        cid = c["id"]
        electricity = elec_shares.get(cid, 0.0)
        water = water_shares.get(cid, 0.0)
        garbage = garbage_shares.get(cid, 0.0)
        gas_hotel = hotel_gas_shares.get(cid, 0.0)
        gas_gf = gf_gas_shares.get(cid, 0.0)
        gas_ff = ff_gas_shares.get(cid, 0.0)
        total = electricity + water + garbage + gas_hotel + gas_gf + gas_ff

        results.append({
            "company_id": cid,
            "company_name": c["name"],
            "electricity": round(electricity, 2),
            "water": round(water, 2),
            "garbage": round(garbage, 2),
            "gas_hotel": round(gas_hotel, 2),
            "gas_ground_floor": round(gas_gf, 2),
            "gas_first_floor": round(gas_ff, 2),
            "total": round(total, 2),
        })

    return results
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_engine.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add engine.py tests/test_engine.py
git commit -m "feat: core allocation engine with weighted distribution"
```

---

### Task 3: Excel Export

**Files:**
- Create: `excel_export.py`
- Create: `tests/test_excel_export.py`

- [ ] **Step 1: Write failing tests for Excel export**

Create `tests/test_excel_export.py`:

```python
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


@pytest.fixture
def defaults():
    return {"elevator_cost": 400}


def test_generate_excel_creates_file(allocation_results, monthly_input, ratios, companies, defaults):
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    try:
        generate_excel(path, allocation_results, monthly_input, ratios, companies, defaults)
        assert os.path.exists(path)
    finally:
        os.unlink(path)


def test_excel_has_three_sheets(allocation_results, monthly_input, ratios, companies, defaults):
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    try:
        generate_excel(path, allocation_results, monthly_input, ratios, companies, defaults)
        wb = openpyxl.load_workbook(path)
        assert len(wb.sheetnames) == 3
        assert "Summary" in wb.sheetnames
        assert "Detailed Breakdown" in wb.sheetnames
        assert "Calculation Details" in wb.sheetnames
    finally:
        os.unlink(path)


def test_summary_sheet_has_correct_data(allocation_results, monthly_input, ratios, companies, defaults):
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    try:
        generate_excel(path, allocation_results, monthly_input, ratios, companies, defaults)
        wb = openpyxl.load_workbook(path)
        ws = wb["Summary"]
        # Row 1 is header, rows 2-4 are data
        assert ws.cell(row=2, column=1).value == "Company A"
        assert ws.cell(row=2, column=2).value == 260.0
        assert ws.cell(row=4, column=2).value == 1040.0  # Hotel total
    finally:
        os.unlink(path)


def test_detailed_sheet_has_all_columns(allocation_results, monthly_input, ratios, companies, defaults):
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    try:
        generate_excel(path, allocation_results, monthly_input, ratios, companies, defaults)
        wb = openpyxl.load_workbook(path)
        ws = wb["Detailed Breakdown"]
        headers = [ws.cell(row=1, column=c).value for c in range(1, 9)]
        assert "Company" in headers
        assert "Electricity" in headers
        assert "Water" in headers
        assert "Garbage" in headers
        assert "Total" in headers
    finally:
        os.unlink(path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_excel_export.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement excel_export.py**

```python
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter


def _style_header(ws, row, col_count):
    header_font = Font(bold=True, size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font_white = Font(bold=True, size=11, color="FFFFFF")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    for col in range(1, col_count + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = thin_border


def _style_data_cell(cell, is_currency=False):
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    cell.border = thin_border
    if is_currency:
        cell.number_format = "#,##0.00"
        cell.alignment = Alignment(horizontal="right")


def _write_summary_sheet(wb, results):
    ws = wb.create_sheet("Summary")

    headers = ["Company", "Total Payment (RON)"]
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _style_header(ws, 1, len(headers))

    for i, r in enumerate(results, 2):
        ws.cell(row=i, column=1, value=r["company_name"])
        _style_data_cell(ws.cell(row=i, column=1))
        ws.cell(row=i, column=2, value=r["total"])
        _style_data_cell(ws.cell(row=i, column=2), is_currency=True)

    # Total row
    total_row = len(results) + 2
    ws.cell(row=total_row, column=1, value="TOTAL")
    ws.cell(row=total_row, column=1).font = Font(bold=True)
    ws.cell(row=total_row, column=2, value=sum(r["total"] for r in results))
    ws.cell(row=total_row, column=2).font = Font(bold=True)
    ws.cell(row=total_row, column=2).number_format = "#,##0.00"

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 20


def _write_detailed_sheet(wb, results):
    ws = wb.create_sheet("Detailed Breakdown")

    headers = ["Company", "Electricity", "Water", "Garbage",
               "Gas (Hotel)", "Gas (Ground Floor)", "Gas (First Floor)", "Total"]
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    _style_header(ws, 1, len(headers))

    expense_keys = ["electricity", "water", "garbage",
                    "gas_hotel", "gas_ground_floor", "gas_first_floor", "total"]

    for i, r in enumerate(results, 2):
        ws.cell(row=i, column=1, value=r["company_name"])
        _style_data_cell(ws.cell(row=i, column=1))
        for j, key in enumerate(expense_keys, 2):
            ws.cell(row=i, column=j, value=r[key])
            _style_data_cell(ws.cell(row=i, column=j), is_currency=True)

    # Total row
    total_row = len(results) + 2
    ws.cell(row=total_row, column=1, value="TOTAL")
    ws.cell(row=total_row, column=1).font = Font(bold=True)
    for j, key in enumerate(expense_keys, 2):
        ws.cell(row=total_row, column=j, value=sum(r[key] for r in results))
        ws.cell(row=total_row, column=j).font = Font(bold=True)
        ws.cell(row=total_row, column=j).number_format = "#,##0.00"

    ws.column_dimensions["A"].width = 25
    for col in range(2, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18


def _write_calculation_sheet(wb, results, monthly_input, ratios, companies, defaults):
    ws = wb.create_sheet("Calculation Details")
    row = 1

    # Section 1: Input Values
    ws.cell(row=row, column=1, value="INPUT VALUES")
    ws.cell(row=row, column=1).font = Font(bold=True, size=12)
    row += 1

    input_labels = [
        ("Electricity Total", monthly_input["electricity_total"]),
        ("Garbage Total", monthly_input["garbage_total"]),
        ("Water Total", monthly_input["water_total"]),
        ("Hotel Gas Total", monthly_input["hotel_gas_total"]),
        ("Ground Floor Gas Total", monthly_input["ground_floor_gas_total"]),
        ("First Floor Gas Total", monthly_input["first_floor_gas_total"]),
        ("External Water Deduction", monthly_input.get("external_water_deduction", 0)),
        ("External Electricity Contribution", monthly_input.get("external_electricity_contribution", 0)),
        ("Elevator Cost (informational)", defaults.get("elevator_cost", 400)),
    ]
    for label, value in input_labels:
        ws.cell(row=row, column=1, value=label)
        ws.cell(row=row, column=2, value=value)
        ws.cell(row=row, column=2).number_format = "#,##0.00"
        row += 1

    row += 1

    # Section 2: Allocation Ratios
    ws.cell(row=row, column=1, value="ALLOCATION RATIOS")
    ws.cell(row=row, column=1).font = Font(bold=True, size=12)
    row += 1

    for expense_type, weights in ratios.items():
        ws.cell(row=row, column=1, value=expense_type.capitalize())
        ws.cell(row=row, column=2, value=f"{weights['sqm_weight']}% sqm + {weights['headcount_weight']}% headcount")
        row += 1

    row += 1

    # Section 3: Per-company breakdown
    active = [c for c in companies if c["active"]]
    ws.cell(row=row, column=1, value="COMPANY ALLOCATION DETAILS")
    ws.cell(row=row, column=1).font = Font(bold=True, size=12)
    row += 1

    headers = ["Company", "Area (m2)", "Headcount", "sqm % of total", "HC % of total"]
    for col, header in enumerate(headers, 1):
        ws.cell(row=row, column=col, value=header)
    _style_header(ws, row, len(headers))
    row += 1

    total_sqm = sum(c["area_m2"] for c in active)
    total_hc = sum(c["headcount_default"] for c in active)

    for c in active:
        ws.cell(row=row, column=1, value=c["name"])
        ws.cell(row=row, column=2, value=c["area_m2"])
        ws.cell(row=row, column=3, value=c["headcount_default"])
        ws.cell(row=row, column=4, value=round(c["area_m2"] / total_sqm * 100, 2) if total_sqm else 0)
        ws.cell(row=row, column=4).number_format = "0.00%"
        ws.cell(row=row, column=5, value=round(c["headcount_default"] / total_hc * 100, 2) if total_hc else 0)
        ws.cell(row=row, column=5).number_format = "0.00%"
        row += 1

    # Totals
    ws.cell(row=row, column=1, value="TOTAL")
    ws.cell(row=row, column=1).font = Font(bold=True)
    ws.cell(row=row, column=2, value=total_sqm)
    ws.cell(row=row, column=2).font = Font(bold=True)
    ws.cell(row=row, column=3, value=total_hc)
    ws.cell(row=row, column=3).font = Font(bold=True)

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 18


def generate_excel(filepath, results, monthly_input, ratios, companies, defaults):
    """Generate a 3-sheet Excel workbook with cost allocation results."""
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    _write_summary_sheet(wb, results)
    _write_detailed_sheet(wb, results)
    _write_calculation_sheet(wb, results, monthly_input, ratios, companies, defaults)

    wb.save(filepath)
    return filepath
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_excel_export.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add excel_export.py tests/test_excel_export.py
git commit -m "feat: Excel export with 3 sheets (summary, detail, calculation)"
```

---

### Task 4: Streamlit UI

**Files:**
- Create: `app.py`

- [ ] **Step 1: Create app.py**

```python
import streamlit as st
import tempfile
import os
from datetime import datetime
from data_manager import (
    load_companies, save_companies, load_settings, save_settings,
    add_company, update_company, get_active_companies,
)
from engine import allocate_costs
from excel_export import generate_excel


st.set_page_config(page_title="Premier Group - Shared Cost Engine", layout="wide")
st.title("Premier Group - Shared Cost Engine")

# Load data
if "companies" not in st.session_state:
    st.session_state.companies = load_companies()
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()


def reload_data():
    st.session_state.companies = load_companies()
    st.session_state.settings = load_settings()


tab1, tab2, tab3 = st.tabs(["Monthly Input", "Company Management", "Settings"])

# =============================================================================
# TAB 1: Monthly Input
# =============================================================================
with tab1:
    st.header("Monthly Cost Allocation")

    col_date1, col_date2 = st.columns(2)
    with col_date1:
        month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1,
                             format_func=lambda m: datetime(2026, m, 1).strftime("%B"))
    with col_date2:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)

    st.subheader("Invoice Totals (RON)")

    col1, col2, col3 = st.columns(3)
    with col1:
        electricity_total = st.number_input("Electricity Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        water_total = st.number_input("Water Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    with col2:
        garbage_total = st.number_input("Garbage Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        hotel_gas_total = st.number_input("Hotel Gas Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    with col3:
        ground_floor_gas_total = st.number_input("Ground Floor Gas Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        first_floor_gas_total = st.number_input("First Floor Gas Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")

    st.subheader("Adjustments (RON)")
    adj1, adj2 = st.columns(2)
    with adj1:
        external_water = st.number_input("External Water Deduction", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    with adj2:
        external_electricity = st.number_input("External Electricity Contribution", min_value=0.0, value=0.0, step=0.01, format="%.2f")

    # Headcount overrides
    st.subheader("Headcount (this month)")
    active_companies = get_active_companies()
    headcount_overrides = {}
    cols = st.columns(4)
    for i, c in enumerate(active_companies):
        with cols[i % 4]:
            hc = st.number_input(
                c["name"],
                min_value=0,
                value=c["headcount_default"],
                step=1,
                key=f"hc_{c['id']}",
            )
            if hc != c["headcount_default"]:
                headcount_overrides[c["id"]] = hc

    st.divider()

    if st.button("Generate Excel Report", type="primary", use_container_width=True):
        monthly_input = {
            "electricity_total": electricity_total,
            "garbage_total": garbage_total,
            "water_total": water_total,
            "hotel_gas_total": hotel_gas_total,
            "ground_floor_gas_total": ground_floor_gas_total,
            "first_floor_gas_total": first_floor_gas_total,
            "external_water_deduction": external_water,
            "external_electricity_contribution": external_electricity,
        }

        settings = st.session_state.settings
        results = allocate_costs(
            st.session_state.companies,
            settings["ratios"],
            monthly_input,
            settings["defaults"],
            headcount_overrides if headcount_overrides else None,
        )

        # Show preview
        st.subheader("Allocation Preview")
        preview_data = {
            "Company": [r["company_name"] for r in results],
            "Electricity": [r["electricity"] for r in results],
            "Water": [r["water"] for r in results],
            "Garbage": [r["garbage"] for r in results],
            "Gas (Hotel)": [r["gas_hotel"] for r in results],
            "Gas (GF)": [r["gas_ground_floor"] for r in results],
            "Gas (1F)": [r["gas_first_floor"] for r in results],
            "Total": [r["total"] for r in results],
        }
        st.dataframe(preview_data, use_container_width=True)

        # Generate Excel
        month_name = datetime(year, month, 1).strftime("%B")
        filename = f"Premier_Group_Cost_Allocation_{year}_{month:02d}_{month_name}.xlsx"
        tmp_path = os.path.join(tempfile.gettempdir(), filename)

        generate_excel(
            tmp_path, results, monthly_input,
            settings["ratios"], active_companies, settings["defaults"],
        )

        with open(tmp_path, "rb") as f:
            st.download_button(
                label=f"Download {filename}",
                data=f,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

# =============================================================================
# TAB 2: Company Management
# =============================================================================
with tab2:
    st.header("Company Management")

    companies = st.session_state.companies

    # Display companies table
    st.subheader("Current Companies")
    for i, c in enumerate(companies):
        status = "Active" if c["active"] else "Inactive"
        status_color = "green" if c["active"] else "red"

        with st.expander(f"{'🟢' if c['active'] else '🔴'} {c['name']} — {c['floor'].replace('_', ' ').title()} — {c['area_m2']} m2"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("Name", value=c["name"], key=f"edit_name_{c['id']}")
                new_area = st.number_input("Area (m2)", value=c["area_m2"], key=f"edit_area_{c['id']}", step=0.01)
                new_hc = st.number_input("Default Headcount", value=c["headcount_default"], key=f"edit_hc_{c['id']}", step=1)
            with col2:
                floor_options = ["ground_floor", "first_floor", "mezzanine", "hotel"]
                new_floor = st.selectbox("Floor", floor_options, index=floor_options.index(c["floor"]), key=f"edit_floor_{c['id']}")
                new_building = st.text_input("Building", value=c["building"], key=f"edit_building_{c['id']}")
                new_heating = st.checkbox("Has Heating (Gas)", value=c["has_heating"], key=f"edit_heating_{c['id']}")
            with col3:
                new_elec = st.checkbox("Electricity Eligible", value=c["electricity_eligible"], key=f"edit_elec_{c['id']}")
                new_water = st.checkbox("Water Eligible", value=c["water_eligible"], key=f"edit_water_{c['id']}")
                new_garbage = st.checkbox("Garbage Eligible", value=c["garbage_eligible"], key=f"edit_garbage_{c['id']}")
                new_active = st.checkbox("Active", value=c["active"], key=f"edit_active_{c['id']}")

            if st.button("Save Changes", key=f"save_{c['id']}"):
                update_company(c["id"], {
                    "name": new_name,
                    "area_m2": new_area,
                    "headcount_default": new_hc,
                    "floor": new_floor,
                    "building": new_building,
                    "has_heating": new_heating,
                    "electricity_eligible": new_elec,
                    "water_eligible": new_water,
                    "garbage_eligible": new_garbage,
                    "active": new_active,
                })
                reload_data()
                st.success(f"Updated {new_name}")
                st.rerun()

    # Add new company
    st.divider()
    st.subheader("Add New Company")

    with st.form("add_company_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            add_name = st.text_input("Company Name")
            add_area = st.number_input("Area (m2)", min_value=0.0, step=0.01)
            add_hc = st.number_input("Default Headcount", min_value=0, step=1, value=1)
        with col2:
            add_floor = st.selectbox("Floor", ["ground_floor", "first_floor", "mezzanine", "hotel"])
            add_building = st.text_input("Building", value="C4")
            add_heating = st.checkbox("Has Heating (Gas)", value=True)
        with col3:
            add_elec = st.checkbox("Electricity Eligible", value=True)
            add_water = st.checkbox("Water Eligible", value=True)
            add_garbage = st.checkbox("Garbage Eligible", value=True)

        submitted = st.form_submit_button("Add Company", type="primary")
        if submitted and add_name:
            company_id = add_name.lower().replace(" ", "-").replace("&", "and")
            new_company = {
                "id": company_id,
                "name": add_name,
                "area_m2": add_area,
                "headcount_default": add_hc,
                "building": add_building,
                "floor": add_floor,
                "has_heating": add_heating,
                "electricity_eligible": add_elec,
                "water_eligible": add_water,
                "garbage_eligible": add_garbage,
                "active": True,
            }
            add_company(new_company)
            reload_data()
            st.success(f"Added {add_name}")
            st.rerun()

# =============================================================================
# TAB 3: Settings
# =============================================================================
with tab3:
    st.header("Settings")

    settings = st.session_state.settings

    st.subheader("Allocation Ratios")
    st.caption("sqm % + headcount % must equal 100 for each expense type")

    ratios_changed = False
    for expense_type in ["electricity", "gas", "water", "garbage"]:
        st.markdown(f"**{expense_type.capitalize()}**")
        col1, col2 = st.columns(2)
        current = settings["ratios"][expense_type]
        with col1:
            new_sqm = st.slider(
                f"sqm % ({expense_type})",
                min_value=0, max_value=100,
                value=current["sqm_weight"],
                key=f"ratio_sqm_{expense_type}",
            )
        with col2:
            st.metric("headcount %", 100 - new_sqm)

        if new_sqm != current["sqm_weight"]:
            settings["ratios"][expense_type]["sqm_weight"] = new_sqm
            settings["ratios"][expense_type]["headcount_weight"] = 100 - new_sqm
            ratios_changed = True

    st.divider()
    st.subheader("Default Values")

    new_elevator = st.number_input(
        "Elevator Cost (RON)",
        min_value=0.0,
        value=float(settings["defaults"]["elevator_cost"]),
        step=10.0,
        format="%.2f",
    )
    if new_elevator != settings["defaults"]["elevator_cost"]:
        settings["defaults"]["elevator_cost"] = new_elevator
        ratios_changed = True

    if ratios_changed:
        if st.button("Save Settings", type="primary"):
            save_settings(settings)
            reload_data()
            st.success("Settings saved!")
            st.rerun()
```

- [ ] **Step 2: Smoke test the app**

Run: `streamlit run app.py`
Expected: App opens in browser with 3 tabs, no errors. Verify:
- Tab 1: All input fields visible, generate button works
- Tab 2: 13 companies listed, add form works
- Tab 3: Ratio sliders work, elevator cost editable

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: Streamlit UI with monthly input, company management, and settings"
```

---

### Task 5: Integration Test and Polish

**Files:**
- Modify: `app.py` (if any fixes needed)
- Modify: `engine.py` (if any fixes needed)

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: End-to-end manual test with real bill data**

Run `streamlit run app.py` and enter the actual February 2026 bill values:
- Electricity: 3598.89
- Garbage: 407.74
- Water: 855.60
- Hotel Gas: 4021.74
- Ground Floor Gas: 2583.53
- First Floor Gas: 3172.14
- External water deduction: 0 (adjust if known)
- External electricity contribution: 0 (adjust if known)

Verify:
- All 13 companies appear in preview
- Totals match input minus deductions
- Hotel gas goes only to Hotel
- GF gas excludes Kolnberg
- 1F gas excludes Paul George Cata
- Excel downloads with 3 correct sheets

- [ ] **Step 3: Commit final state**

```bash
git add -A
git commit -m "feat: complete shared cost engine v1.0"
```
