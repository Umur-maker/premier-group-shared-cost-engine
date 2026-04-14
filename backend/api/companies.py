"""Company CRUD endpoints."""

import json
import re
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from backend.core.data_manager import (
    load_companies, add_company, update_company, get_active_companies, save_companies,
)

router = APIRouter(prefix="/api/companies", tags=["companies"])


class CompanyCreate(BaseModel):
    name: str
    area_m2: float
    headcount_default: int = 1
    building: str = "C4"
    floor: str = "ground_floor"
    has_heating: bool = True
    electricity_eligible: bool = True
    water_eligible: bool = True
    garbage_eligible: bool = True
    consumables_eligible: bool = False
    printer_eligible: bool = False
    internet_eligible: bool = False
    office_no: str = ""
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    beginning_date: str = ""
    expiration_date: str = ""
    notes: str = ""
    monthly_rent_eur: float = 0
    maintenance_rate_eur: float = 0


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    area_m2: Optional[float] = None
    headcount_default: Optional[int] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    has_heating: Optional[bool] = None
    electricity_eligible: Optional[bool] = None
    water_eligible: Optional[bool] = None
    garbage_eligible: Optional[bool] = None
    consumables_eligible: Optional[bool] = None
    printer_eligible: Optional[bool] = None
    internet_eligible: Optional[bool] = None
    active: Optional[bool] = None
    office_no: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    beginning_date: Optional[str] = None
    expiration_date: Optional[str] = None
    notes: Optional[str] = None
    monthly_rent_eur: Optional[float] = None
    maintenance_rate_eur: Optional[float] = None


@router.get("")
def list_companies():
    return load_companies()


@router.post("", status_code=201)
def create_company(body: CompanyCreate):
    companies = load_companies()
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Company name is required.")
    if len(name) > 200:
        raise HTTPException(400, "Company name must be 200 characters or less.")
    company_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if any(c["id"] == company_id for c in companies):
        raise HTTPException(409, f"Company ID '{company_id}' already exists.")
    if any(c["name"].strip().lower() == name.lower() for c in companies):
        raise HTTPException(409, f"Company name '{name}' already exists.")
    if body.area_m2 <= 0:
        raise HTTPException(400, "Area must be greater than 0.")

    new_company = {
        "id": company_id,
        "name": name,
        "area_m2": body.area_m2,
        "headcount_default": body.headcount_default,
        "building": body.building,
        "floor": body.floor,
        "has_heating": body.has_heating,
        "electricity_eligible": body.electricity_eligible,
        "water_eligible": body.water_eligible,
        "garbage_eligible": body.garbage_eligible,
        "consumables_eligible": body.consumables_eligible,
        "printer_eligible": body.printer_eligible,
        "internet_eligible": body.internet_eligible,
        "active": True,
        "office_no": body.office_no,
        "contact_person": body.contact_person,
        "phone": body.phone,
        "email": body.email,
        "beginning_date": body.beginning_date,
        "expiration_date": body.expiration_date,
        "notes": body.notes,
        "monthly_rent_eur": body.monthly_rent_eur,
        "maintenance_rate_eur": body.maintenance_rate_eur,
    }
    try:
        add_company(new_company)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return new_company


@router.put("/{company_id}")
def edit_company(company_id: str, body: CompanyUpdate):
    companies = load_companies()
    if not any(c["id"] == company_id for c in companies):
        raise HTTPException(404, f"Company '{company_id}' not found.")
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "No fields to update.")
    if "name" in fields:
        fields["name"] = fields["name"].strip()
        if not fields["name"]:
            raise HTTPException(400, "Company name cannot be empty.")
        if len(fields["name"]) > 200:
            raise HTTPException(400, "Company name must be 200 characters or less.")
    if "area_m2" in fields and fields["area_m2"] <= 0:
        raise HTTPException(400, "Area must be greater than 0.")
    update_company(company_id, fields)
    return {"status": "updated", "id": company_id}


@router.delete("/{company_id}")
def deactivate(company_id: str):
    companies = load_companies()
    if not any(c["id"] == company_id for c in companies):
        raise HTTPException(404, f"Company '{company_id}' not found.")
    update_company(company_id, {"active": False})
    return {"status": "deactivated", "id": company_id}


@router.post("/import")
async def import_companies(file: UploadFile = File(...)):
    """Import companies from a JSON file, replacing all existing companies."""
    try:
        content = await file.read()
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid JSON file.")

    if not isinstance(data, list):
        raise HTTPException(400, "File must contain a JSON array of companies.")

    required = {"id", "name", "area_m2"}
    for i, company in enumerate(data):
        if not isinstance(company, dict):
            raise HTTPException(400, f"Item {i} is not a valid company object.")
        missing = required - set(company.keys())
        if missing:
            raise HTTPException(400, f"Company '{company.get('name', f'#{i}')}' missing fields: {missing}")

    save_companies(data)
    return {"status": "imported", "count": len(data)}
