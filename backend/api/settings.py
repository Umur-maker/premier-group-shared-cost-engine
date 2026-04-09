"""Settings endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
from backend.core.data_manager import load_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class RatioWeight(BaseModel):
    sqm_weight: int
    headcount_weight: int


class SettingsUpdate(BaseModel):
    ratios: Dict[str, RatioWeight]


@router.get("")
def get_settings():
    return load_settings()


@router.put("")
def update_settings(body: SettingsUpdate):
    required = {"electricity", "gas", "water", "garbage", "consumables"}
    if not required.issubset(set(body.ratios.keys())):
        raise HTTPException(400, f"Must provide all expense types: {sorted(required)}")
    for expense_type, weights in body.ratios.items():
        if weights.sqm_weight + weights.headcount_weight != 100:
            raise HTTPException(400, f"{expense_type}: sqm + person must equal 100")
        if weights.sqm_weight < 0 or weights.headcount_weight < 0:
            raise HTTPException(400, f"{expense_type}: weights cannot be negative")

    settings = load_settings()
    settings["ratios"] = {k: v.model_dump() for k, v in body.ratios.items()}
    save_settings(settings)
    return {"status": "saved", "ratios": settings["ratios"]}
