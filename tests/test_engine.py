import pytest
from engine import allocate_costs, _distribute


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
    expected = round(950 * (0.5 * 40.0 / 310.0 + 0.5 * 2.0 / 14.0), 2)
    assert abs(gf_a["electricity"] - expected) < 0.01


# --- Rounding reconciliation tests ---

def test_distribute_sum_equals_amount_exactly():
    """Verify rounding reconciliation: sum of shares == amount."""
    companies = [
        {"id": f"c{i}", "area_m2": 33.33, "headcount_default": 1}
        for i in range(3)
    ]
    # 100 / 3 = 33.333... each, can't represent exactly in 2 decimals
    result = _distribute(100.0, companies, 50, 50)
    assert sum(result.values()) == 100.0


def test_distribute_sum_with_many_companies():
    """Verify reconciliation with 13 companies."""
    companies = [
        {"id": f"c{i}", "area_m2": 10.0 + i * 3.7, "headcount_default": i + 1}
        for i in range(13)
    ]
    result = _distribute(3598.89, companies, 50, 50)
    assert sum(result.values()) == 3598.89


def test_distribute_returns_empty_for_zero_amount():
    companies = [{"id": "a", "area_m2": 10.0, "headcount_default": 1}]
    result = _distribute(0, companies, 50, 50)
    assert result == {}


def test_distribute_returns_empty_for_no_companies():
    result = _distribute(1000, [], 50, 50)
    assert result == {}


def test_all_outputs_rounded_to_2_decimals(companies, ratios, monthly_input, defaults):
    result = allocate_costs(companies, ratios, monthly_input, defaults)
    for r in result:
        for key in ["electricity", "water", "garbage", "gas_hotel", "gas_ground_floor", "gas_first_floor", "total"]:
            value = r[key]
            assert value == round(value, 2), f"{r['company_name']}.{key} = {value} not rounded to 2 decimals"


def test_headcount_overrides(companies, ratios, monthly_input, defaults):
    """Verify that headcount overrides affect distribution."""
    result_default = allocate_costs(companies, ratios, monthly_input, defaults)
    result_override = allocate_costs(companies, ratios, monthly_input, defaults,
                                     headcount_overrides={"hotel": 20})
    hotel_default = next(r for r in result_default if r["company_id"] == "hotel")
    hotel_override = next(r for r in result_override if r["company_id"] == "hotel")
    # More headcount -> higher share for headcount-weighted expenses
    assert hotel_override["electricity"] > hotel_default["electricity"]


# --- Zero sqm / zero headcount robustness tests ---

def test_distribute_zero_total_sqm():
    """If all companies have 0 sqm, rebalance to 100% headcount."""
    companies = [
        {"id": "a", "area_m2": 0.0, "headcount_default": 2},
        {"id": "b", "area_m2": 0.0, "headcount_default": 3},
    ]
    result = _distribute(1000.0, companies, 50, 50)
    assert sum(result.values()) == 1000.0
    # Should be proportional to headcount only: 2/5 and 3/5
    assert result["a"] == 400.0
    assert result["b"] == 600.0


def test_distribute_zero_total_headcount():
    """If all companies have 0 headcount, rebalance to 100% sqm."""
    companies = [
        {"id": "a", "area_m2": 40.0, "headcount_default": 0},
        {"id": "b", "area_m2": 60.0, "headcount_default": 0},
    ]
    result = _distribute(1000.0, companies, 50, 50)
    assert sum(result.values()) == 1000.0
    assert result["a"] == 400.0
    assert result["b"] == 600.0


def test_distribute_zero_both_sqm_and_headcount():
    """If both are zero, equal split."""
    companies = [
        {"id": "a", "area_m2": 0.0, "headcount_default": 0},
        {"id": "b", "area_m2": 0.0, "headcount_default": 0},
    ]
    result = _distribute(1000.0, companies, 50, 50)
    assert sum(result.values()) == 1000.0
    assert result["a"] == 500.0
    assert result["b"] == 500.0


def test_distribute_zero_both_with_indivisible_amount():
    """Equal split with rounding reconciliation: 100 / 3 = 33.33 + 33.33 + 33.34."""
    companies = [
        {"id": "a", "area_m2": 0.0, "headcount_default": 0},
        {"id": "b", "area_m2": 0.0, "headcount_default": 0},
        {"id": "c", "area_m2": 0.0, "headcount_default": 0},
    ]
    result = _distribute(100.0, companies, 50, 50)
    assert sum(result.values()) == 100.0
