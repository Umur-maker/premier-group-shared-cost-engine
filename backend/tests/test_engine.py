import pytest
from backend.core.engine import allocate_costs, _distribute


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
        "external_electricity": 50.0,
        "external_water": 100.0,
        "external_garbage": 0.0,
        "external_hotel_gas": 0.0,
        "external_gf_gas": 0.0,
        "external_ff_gas": 0.0,
    }


def test_allocate_costs_returns_all_companies(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    assert len(result) == 4


def test_electricity_sums_to_net(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    elec_sum = sum(r["electricity"] for r in result)
    expected = monthly_input["electricity_total"] - monthly_input["external_electricity"]
    assert elec_sum == expected


def test_water_sums_to_net(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    water_sum = sum(r["water"] for r in result)
    expected = monthly_input["water_total"] - monthly_input["external_water"]
    assert water_sum == expected


def test_garbage_sums_to_net(companies, ratios, monthly_input):
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
    non_total_keys = ("company_id", "company_name", "total")
    for r in result:
        expected = round(sum(v for k, v in r.items() if k not in non_total_keys), 2)
        assert r["total"] == expected


def test_inactive_companies_excluded(companies, ratios, monthly_input):
    companies[0]["active"] = False
    result = allocate_costs(companies, ratios, monthly_input)
    assert len(result) == 3


def test_all_outputs_rounded_to_2_decimals(companies, ratios, monthly_input):
    result = allocate_costs(companies, ratios, monthly_input)
    for r in result:
        for key in ["electricity", "water", "garbage", "gas_hotel", "gas_ground_floor", "gas_first_floor", "total"]:
            assert r[key] == round(r[key], 2)


# --- 6 external usage fields ---

def test_all_six_external_usages():
    companies = [
        {"id": "a", "name": "A", "area_m2": 50.0, "headcount_default": 2,
         "building": "C4", "floor": "ground_floor", "has_heating": True,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "active": True},
        {"id": "hotel", "name": "Hotel", "area_m2": 100.0, "headcount_default": 5,
         "building": "C1", "floor": "hotel", "has_heating": True,
         "electricity_eligible": True, "water_eligible": True, "garbage_eligible": True, "active": True},
    ]
    ratios = {
        "electricity": {"sqm_weight": 50, "headcount_weight": 50},
        "gas": {"sqm_weight": 80, "headcount_weight": 20},
        "water": {"sqm_weight": 50, "headcount_weight": 50},
        "garbage": {"sqm_weight": 50, "headcount_weight": 50},
    }
    monthly_input = {
        "electricity_total": 1000.0, "water_total": 500.0, "garbage_total": 300.0,
        "hotel_gas_total": 400.0, "ground_floor_gas_total": 200.0, "first_floor_gas_total": 0.0,
        "external_electricity": 100.0, "external_water": 50.0, "external_garbage": 30.0,
        "external_hotel_gas": 40.0, "external_gf_gas": 20.0, "external_ff_gas": 0.0,
    }
    result = allocate_costs(companies, ratios, monthly_input)
    assert sum(r["electricity"] for r in result) == 900.0
    assert sum(r["water"] for r in result) == 450.0
    assert sum(r["garbage"] for r in result) == 270.0
    hotel = next(r for r in result if r["company_id"] == "hotel")
    assert hotel["gas_hotel"] == 360.0  # 400 - 40
    a = next(r for r in result if r["company_id"] == "a")
    assert a["gas_ground_floor"] == 180.0  # 200 - 20


def test_negative_external_raises_error(companies, ratios):
    bad = {
        "electricity_total": 40.0, "water_total": 0.0, "garbage_total": 0.0,
        "hotel_gas_total": 0.0, "ground_floor_gas_total": 0.0, "first_floor_gas_total": 0.0,
        "external_electricity": 50.0, "external_water": 0.0, "external_garbage": 0.0,
        "external_hotel_gas": 0.0, "external_gf_gas": 0.0, "external_ff_gas": 0.0,
    }
    with pytest.raises(ValueError, match="negative"):
        allocate_costs(companies, ratios, bad)


def test_zero_net_is_valid(companies, ratios):
    inp = {
        "electricity_total": 50.0, "water_total": 100.0, "garbage_total": 0.0,
        "hotel_gas_total": 0.0, "ground_floor_gas_total": 0.0, "first_floor_gas_total": 0.0,
        "external_electricity": 50.0, "external_water": 100.0, "external_garbage": 0.0,
        "external_hotel_gas": 0.0, "external_gf_gas": 0.0, "external_ff_gas": 0.0,
    }
    result = allocate_costs(companies, ratios, inp)
    assert all(r["electricity"] == 0.0 for r in result)
    assert all(r["water"] == 0.0 for r in result)


def test_all_inactive_returns_empty(companies, ratios, monthly_input):
    for c in companies:
        c["active"] = False
    assert allocate_costs(companies, ratios, monthly_input) == []


# --- Rounding ---

def test_distribute_sum_equals_amount():
    cs = [{"id": f"c{i}", "area_m2": 33.33, "headcount_default": 1} for i in range(3)]
    assert sum(_distribute(100.0, cs, 50, 50).values()) == 100.0


def test_distribute_sum_13_companies():
    cs = [{"id": f"c{i}", "area_m2": 10.0 + i * 3.7, "headcount_default": i + 1} for i in range(13)]
    assert sum(_distribute(3598.89, cs, 50, 50).values()) == 3598.89


def test_distribute_zero_sqm_fallback():
    cs = [{"id": "a", "area_m2": 0.0, "headcount_default": 2},
          {"id": "b", "area_m2": 0.0, "headcount_default": 3}]
    r = _distribute(1000.0, cs, 50, 50)
    assert sum(r.values()) == 1000.0
    assert r["a"] == 400.0


def test_distribute_zero_both_equal_split():
    cs = [{"id": "a", "area_m2": 0.0, "headcount_default": 0},
          {"id": "b", "area_m2": 0.0, "headcount_default": 0},
          {"id": "c", "area_m2": 0.0, "headcount_default": 0}]
    assert sum(_distribute(100.0, cs, 50, 50).values()) == 100.0


# --- Legacy field compatibility ---

def test_legacy_field_names(companies, ratios):
    """Old field names (external_water_deduction etc.) still work."""
    inp = {
        "electricity_total": 1000.0, "water_total": 500.0, "garbage_total": 400.0,
        "hotel_gas_total": 300.0, "ground_floor_gas_total": 200.0, "first_floor_gas_total": 250.0,
        "external_electricity_contribution": 50.0,
        "external_water_deduction": 100.0,
    }
    result = allocate_costs(companies, ratios, inp)
    assert sum(r["electricity"] for r in result) == 950.0
    assert sum(r["water"] for r in result) == 400.0
