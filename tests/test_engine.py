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


def test_allocate_costs_returns_all_companies(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    assert len(result) == 4
    assert all("company_id" in r for r in result)
    assert all("company_name" in r for r in result)
    assert all("total" in r for r in result)


def test_allocate_costs_has_all_expense_types(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    for r in result:
        assert "electricity" in r
        assert "water" in r
        assert "garbage" in r
        assert "gas_hotel" in r
        assert "gas_ground_floor" in r
        assert "gas_first_floor" in r


def test_electricity_sums_to_total_minus_external(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    elec_sum = sum(r["electricity"] for r in result)
    expected = monthly_input["electricity_total"] - monthly_input["external_electricity_contribution"]
    assert elec_sum == expected


def test_water_sums_to_total_minus_external(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    water_sum = sum(r["water"] for r in result)
    expected = monthly_input["water_total"] - monthly_input["external_water_deduction"]
    assert water_sum == expected


def test_garbage_sums_to_total(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    garbage_sum = sum(r["garbage"] for r in result)
    assert garbage_sum == monthly_input["garbage_total"]


def test_hotel_gas_only_to_hotel(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    for r in result:
        if r["company_id"] == "hotel":
            assert r["gas_hotel"] == 300.0
        else:
            assert r["gas_hotel"] == 0.0


def test_ground_floor_gas_excludes_no_heating(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    gf_b = next(r for r in result if r["company_id"] == "gf-b")
    assert gf_b["gas_ground_floor"] == 0.0
    gf_a = next(r for r in result if r["company_id"] == "gf-a")
    assert gf_a["gas_ground_floor"] == 200.0


def test_first_floor_gas_only_to_first_floor(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    ff_a = next(r for r in result if r["company_id"] == "ff-a")
    assert ff_a["gas_first_floor"] == 250.0
    for r in result:
        if r["company_id"] != "ff-a":
            assert r["gas_first_floor"] == 0.0


def test_total_is_sum_of_all_expenses(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    for r in result:
        expected_total = round(
            r["electricity"] + r["water"] + r["garbage"]
            + r["gas_hotel"] + r["gas_ground_floor"] + r["gas_first_floor"], 2
        )
        assert r["total"] == expected_total


def test_inactive_companies_excluded(companies, ratios, monthly_input):
    companies[0]["active"] = False
    result = allocate_costs(companies, ratios, monthly_input)
    assert len(result) == 3
    assert all(r["company_id"] != "gf-a" for r in result)


def test_weighted_distribution_electricity(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    remaining = 1000.0 - 50.0
    gf_a = next(r for r in result if r["company_id"] == "gf-a")
    expected = round(remaining * (0.5 * 40.0 / 310.0 + 0.5 * 2.0 / 14.0), 2)
    assert abs(gf_a["electricity"] - expected) < 0.01


# --- Rounding reconciliation tests ---

def test_distribute_sum_equals_amount_exactly():
    companies = [
        {"id": f"c{i}", "area_m2": 33.33, "headcount_default": 1}
        for i in range(3)
    ]
    result = _distribute(100.0, companies, 50, 50)
    assert sum(result.values()) == 100.0


def test_distribute_sum_with_many_companies():
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


def test_all_outputs_rounded_to_2_decimals(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    for r in result:
        for key in ["electricity", "water", "garbage", "gas_hotel", "gas_ground_floor", "gas_first_floor", "total"]:
            value = r[key]
            assert value == round(value, 2), f"{r['company_name']}.{key} = {value} not rounded"


def test_headcount_overrides(companies, ratios, monthly_input):
    result_default = allocate_costs(companies, ratios, monthly_input)
    result_override = allocate_costs(companies, ratios, monthly_input,
                                     headcount_overrides={"hotel": 20})
    hotel_default = next(r for r in result_default if r["company_id"] == "hotel")
    hotel_override = next(r for r in result_override if r["company_id"] == "hotel")
    assert hotel_override["electricity"] > hotel_default["electricity"]


# --- Zero sqm / zero headcount robustness tests ---

def test_distribute_zero_total_sqm():
    companies = [
        {"id": "a", "area_m2": 0.0, "headcount_default": 2},
        {"id": "b", "area_m2": 0.0, "headcount_default": 3},
    ]
    result = _distribute(1000.0, companies, 50, 50)
    assert sum(result.values()) == 1000.0
    assert result["a"] == 400.0
    assert result["b"] == 600.0


def test_distribute_zero_total_headcount():
    companies = [
        {"id": "a", "area_m2": 40.0, "headcount_default": 0},
        {"id": "b", "area_m2": 60.0, "headcount_default": 0},
    ]
    result = _distribute(1000.0, companies, 50, 50)
    assert sum(result.values()) == 1000.0
    assert result["a"] == 400.0
    assert result["b"] == 600.0


def test_distribute_zero_both_sqm_and_headcount():
    companies = [
        {"id": "a", "area_m2": 0.0, "headcount_default": 0},
        {"id": "b", "area_m2": 0.0, "headcount_default": 0},
    ]
    result = _distribute(1000.0, companies, 50, 50)
    assert sum(result.values()) == 1000.0
    assert result["a"] == 500.0
    assert result["b"] == 500.0


def test_distribute_zero_both_with_indivisible_amount():
    companies = [
        {"id": "a", "area_m2": 0.0, "headcount_default": 0},
        {"id": "b", "area_m2": 0.0, "headcount_default": 0},
        {"id": "c", "area_m2": 0.0, "headcount_default": 0},
    ]
    result = _distribute(100.0, companies, 50, 50)
    assert sum(result.values()) == 100.0


# --- Negative net amount tests ---

def test_negative_electricity_raises_error(companies, ratios):
    bad_input = {
        "electricity_total": 40.0, "garbage_total": 0.0, "water_total": 0.0,
        "hotel_gas_total": 0.0, "ground_floor_gas_total": 0.0, "first_floor_gas_total": 0.0,
        "external_water_deduction": 0.0, "external_electricity_contribution": 50.0,
    }
    with pytest.raises(ValueError, match="Net electricity amount is negative"):
        allocate_costs(companies, ratios, bad_input)


def test_negative_water_raises_error(companies, ratios):
    bad_input = {
        "electricity_total": 0.0, "garbage_total": 0.0, "water_total": 100.0,
        "hotel_gas_total": 0.0, "ground_floor_gas_total": 0.0, "first_floor_gas_total": 0.0,
        "external_water_deduction": 150.0, "external_electricity_contribution": 0.0,
    }
    with pytest.raises(ValueError, match="Net water amount is negative"):
        allocate_costs(companies, ratios, bad_input)


def test_zero_net_amount_is_valid(companies, ratios):
    input_data = {
        "electricity_total": 50.0, "garbage_total": 0.0, "water_total": 100.0,
        "hotel_gas_total": 0.0, "ground_floor_gas_total": 0.0, "first_floor_gas_total": 0.0,
        "external_water_deduction": 100.0, "external_electricity_contribution": 50.0,
    }
    result = allocate_costs(companies, ratios, input_data)
    assert all(r["electricity"] == 0.0 for r in result)
    assert all(r["water"] == 0.0 for r in result)


def test_all_inactive_returns_empty(companies, ratios, monthly_input):
    for c in companies:
        c["active"] = False
    result = allocate_costs(companies, ratios, monthly_input)
    assert result == []
