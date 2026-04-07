"""Pure allocation engine. No Streamlit, no file I/O. Input -> calculation -> output."""


def _distribute(amount, eligible_companies, sqm_weight, headcount_weight, headcount_overrides=None):
    """Distribute an amount across companies based on weighted sqm + headcount formula.

    Guarantees: sum of returned values == round(amount, 2).
    Rounding difference is applied to the largest share.

    Returns dict of {company_id: share}.
    """
    if not eligible_companies or amount <= 0:
        return {}

    amount = round(amount, 2)
    w_sqm = sqm_weight / 100.0
    w_hc = headcount_weight / 100.0

    total_sqm = sum(c["area_m2"] for c in eligible_companies)
    overrides = headcount_overrides or {}
    total_hc = sum(overrides.get(c["id"], c["headcount_default"]) for c in eligible_companies)

    if total_sqm == 0 and total_hc == 0:
        n = len(eligible_companies)
        result = {c["id"]: round(amount / n, 2) for c in eligible_companies}
        distributed = sum(result.values())
        diff = round(amount - distributed, 2)
        if diff != 0:
            first_id = next(iter(result))
            result[first_id] = round(result[first_id] + diff, 2)
        return result
    elif total_sqm == 0:
        w_sqm, w_hc = 0.0, 1.0
    elif total_hc == 0:
        w_sqm, w_hc = 1.0, 0.0

    result = {}
    for c in eligible_companies:
        sqm_ratio = c["area_m2"] / total_sqm if total_sqm > 0 else 0
        hc = overrides.get(c["id"], c["headcount_default"])
        hc_ratio = hc / total_hc if total_hc > 0 else 0
        result[c["id"]] = round(amount * (w_sqm * sqm_ratio + w_hc * hc_ratio), 2)

    distributed = sum(result.values())
    diff = round(amount - distributed, 2)
    if diff != 0 and result:
        largest_id = max(result, key=result.get)
        result[largest_id] = round(result[largest_id] + diff, 2)

    return result


def _equal_split(amount, eligible_companies):
    """Split amount equally among eligible companies with rounding reconciliation."""
    if not eligible_companies or amount <= 0:
        return {}
    amount = round(amount, 2)
    n = len(eligible_companies)
    result = {c["id"]: round(amount / n, 2) for c in eligible_companies}
    distributed = sum(result.values())
    diff = round(amount - distributed, 2)
    if diff != 0:
        first_id = next(iter(result))
        result[first_id] = round(result[first_id] + diff, 2)
    return result


def _net_amount(total, external):
    """Calculate net amount after external usage. Raises ValueError if negative."""
    net = total - external
    if net < 0:
        raise ValueError(f"Net amount is negative ({net:.2f}). External usage exceeds total.")
    return net


def _filter_eligible(active, category_config):
    """Filter companies based on cost category eligibility rules."""
    eligible = list(active)

    if category_config.get("eligible") == "custom":
        include = category_config.get("include_companies")
        if include:
            eligible = [c for c in eligible if c["id"] in include]
        exclude = category_config.get("exclude_companies", [])
        if exclude:
            eligible = [c for c in eligible if c["id"] not in exclude]

    exclude_floors = category_config.get("exclude_floors", [])
    if exclude_floors:
        eligible = [c for c in eligible if c["floor"] not in exclude_floors]

    return eligible


def allocate_costs(companies, ratios, monthly_input, settings=None, headcount_overrides=None):
    """Main allocation function. Pure function: no I/O, no side effects.

    Args:
        companies: list of company dicts
        ratios: dict with expense type keys, each having sqm_weight/headcount_weight
        monthly_input: dict with all invoice totals and external usage values
        settings: full settings dict (for cost_categories, eur_ron_rate, etc.)
        headcount_overrides: optional dict of {company_id: headcount}

    Returns:
        list of dicts, one per active company, with per-expense and total amounts.
    """
    active = [c for c in companies if c["active"]]
    overrides = headcount_overrides or {}
    cats = (settings or {}).get("cost_categories", {})
    eur_rate = (settings or {}).get("eur_ron_rate", 5.1)

    def _ext(key, legacy_key=None):
        val = monthly_input.get(key, 0)
        if val == 0 and legacy_key:
            val = monthly_input.get(legacy_key, 0)
        return val

    # ── EXISTING UTILITY COSTS ──

    # Electricity
    elec_eligible = [c for c in active if c.get("electricity_eligible", True)]
    elec_amount = _net_amount(
        monthly_input.get("electricity_total", 0),
        _ext("external_electricity", "external_electricity_contribution"),
    )
    elec_shares = _distribute(elec_amount, elec_eligible,
        ratios["electricity"]["sqm_weight"], ratios["electricity"]["headcount_weight"], overrides)

    # Water
    water_eligible = [c for c in active if c.get("water_eligible", True)]
    water_amount = _net_amount(
        monthly_input.get("water_total", 0),
        _ext("external_water", "external_water_deduction"),
    )
    water_shares = _distribute(water_amount, water_eligible,
        ratios["water"]["sqm_weight"], ratios["water"]["headcount_weight"], overrides)

    # Garbage
    garbage_eligible = [c for c in active if c.get("garbage_eligible", True)]
    garbage_amount = _net_amount(
        monthly_input.get("garbage_total", 0),
        _ext("external_garbage"),
    )
    garbage_shares = _distribute(garbage_amount, garbage_eligible,
        ratios["garbage"]["sqm_weight"], ratios["garbage"]["headcount_weight"], overrides)

    # Gas Hotel
    hotel_gas_eligible = [c for c in active if c["floor"] == "hotel" and c.get("has_heating", False)]
    hotel_gas_amount = _net_amount(
        monthly_input.get("hotel_gas_total", 0), _ext("external_hotel_gas"))
    hotel_gas_shares = _distribute(hotel_gas_amount, hotel_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)

    # Gas Ground Floor
    gf_gas_eligible = [c for c in active if c["floor"] == "ground_floor" and c.get("has_heating", False)]
    gf_gas_amount = _net_amount(
        monthly_input.get("ground_floor_gas_total", 0), _ext("external_gf_gas"))
    gf_gas_shares = _distribute(gf_gas_amount, gf_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)

    # Gas First Floor
    ff_gas_eligible = [c for c in active if c["floor"] == "first_floor" and c.get("has_heating", False)]
    ff_gas_amount = _net_amount(
        monthly_input.get("first_floor_gas_total", 0), _ext("external_ff_gas"))
    ff_gas_shares = _distribute(ff_gas_amount, ff_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)

    # ── NEW COST CATEGORIES ──

    # Consumables (weighted, monthly input)
    consumables_amount = monthly_input.get("consumables_total", 0)
    consumables_eligible = _filter_eligible(active, cats.get("consumables", {"eligible": "all"}))
    r_key = cats.get("consumables", {}).get("ratio_key", "consumables")
    cons_ratios = ratios.get(r_key, {"sqm_weight": 50, "headcount_weight": 50})
    consumables_shares = _distribute(consumables_amount, consumables_eligible,
        cons_ratios["sqm_weight"], cons_ratios["headcount_weight"], overrides)

    # Drinking Water (equal split, exclude GF + GBCS)
    drinking_water_amount = monthly_input.get("drinking_water_total", 0)
    dw_config = cats.get("drinking_water", {
        "eligible": "custom", "exclude_companies": ["gbcs"], "exclude_floors": ["ground_floor"]
    })
    drinking_water_eligible = _filter_eligible(active, dw_config)
    drinking_water_shares = _equal_split(drinking_water_amount, drinking_water_eligible)

    # Printer (equal split, specific companies)
    printer_amount = monthly_input.get("printer_total", 0)
    printer_config = cats.get("printer", {
        "eligible": "custom",
        "include_companies": ["premier-capital", "premier-vision", "paul-george-cata"]
    })
    printer_eligible = _filter_eligible(active, printer_config)
    printer_shares = _equal_split(printer_amount, printer_eligible)

    # Internet (equal split, specific companies)
    internet_amount = monthly_input.get("internet_total", 0)
    internet_config = cats.get("internet", {
        "eligible": "custom",
        "include_companies": ["premier-capital", "premier-rise", "premier-vision", "paul-george-cata"]
    })
    internet_eligible = _filter_eligible(active, internet_config)
    internet_shares = _equal_split(internet_amount, internet_eligible)

    # Maintenance (per m², EUR → RON, exclude Premier Capital + PGC + Hotel)
    maint_config = cats.get("maintenance", {
        "eligible": "custom",
        "exclude_companies": ["premier-capital", "paul-george-cata", "hotel"]
    })
    maint_rate = (settings or {}).get("maintenance_rate_eur", 2)
    maint_eligible = _filter_eligible(active, maint_config)
    maintenance_shares = {}
    for c in maint_eligible:
        maintenance_shares[c["id"]] = round(maint_rate * c["area_m2"] * eur_rate, 2)

    # Hotel Rent (fixed EUR → RON, hotel only)
    hotel_rent_eur = (settings or {}).get("hotel_rent_eur", 5250)
    hotel_rent_config = cats.get("hotel_rent", {
        "eligible": "custom", "include_companies": ["hotel"]
    })
    hotel_rent_eligible = _filter_eligible(active, hotel_rent_config)
    hotel_rent_shares = {}
    for c in hotel_rent_eligible:
        hotel_rent_shares[c["id"]] = round(hotel_rent_eur * eur_rate, 2)

    # ── BUILD RESULTS ──
    results = []
    for c in active:
        cid = c["id"]
        r = {
            "company_id": cid,
            "company_name": c["name"],
            "electricity": elec_shares.get(cid, 0.0),
            "water": water_shares.get(cid, 0.0),
            "garbage": garbage_shares.get(cid, 0.0),
            "gas_hotel": hotel_gas_shares.get(cid, 0.0),
            "gas_ground_floor": gf_gas_shares.get(cid, 0.0),
            "gas_first_floor": ff_gas_shares.get(cid, 0.0),
            "consumables": consumables_shares.get(cid, 0.0),
            "drinking_water": drinking_water_shares.get(cid, 0.0),
            "printer": printer_shares.get(cid, 0.0),
            "internet": internet_shares.get(cid, 0.0),
            "maintenance": maintenance_shares.get(cid, 0.0),
            "hotel_rent": hotel_rent_shares.get(cid, 0.0),
        }
        r["total"] = round(sum(v for k, v in r.items() if k not in ("company_id", "company_name")), 2)
        results.append(r)

    return results
