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
