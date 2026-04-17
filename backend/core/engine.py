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
    active = [c for c in companies if c.get("active", False)]
    overrides = headcount_overrides or {}
    cats = (settings or {}).get("cost_categories", {})
    eur_rate = (settings or {}).get("eur_ron_rate", 5.1)
    if not eur_rate or eur_rate <= 0:
        eur_rate = 5.1
    # Defensive: ensure all ratio keys exist with safe defaults
    DEFAULT_RATIO = {"sqm_weight": 50, "headcount_weight": 50}
    ratios = ratios or {}
    for k in ("electricity", "gas", "water", "garbage", "consumables"):
        if k not in ratios:
            ratios[k] = DEFAULT_RATIO.copy()

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

    # Gas First Floor (with optional meeting room split)
    ff_gas_eligible = [c for c in active if c["floor"] == "first_floor" and c.get("has_heating", False)]
    ff_gas_amount = _net_amount(
        monthly_input.get("first_floor_gas_total", 0), _ext("external_ff_gas"))

    meeting = (settings or {}).get("meeting_room", {})
    meeting_active = meeting.get("active", False)
    meeting_m2 = float(meeting.get("area_m2", 0) or 0)
    meeting_floor = meeting.get("floor", "first_floor")

    if meeting_active and meeting_m2 > 0 and meeting_floor == "first_floor" and ff_gas_amount > 0:
        # Identify meeting room user companies (per-company checkbox)
        user_companies = [c for c in ff_gas_eligible if c.get("meeting_room_user", False)]
        user_persons = sum(overrides.get(c["id"], c["headcount_default"]) for c in user_companies)
        floor_m2 = sum(c["area_m2"] for c in ff_gas_eligible)
        floor_persons = sum(overrides.get(c["id"], c["headcount_default"]) for c in ff_gas_eligible)

        # Calculate meeting room's share of net gas using gas weights
        sqm_w = ratios["gas"]["sqm_weight"] / 100.0
        hc_w = ratios["gas"]["headcount_weight"] / 100.0
        m2_ratio = meeting_m2 / (floor_m2 + meeting_m2) if (floor_m2 + meeting_m2) > 0 else 0
        person_ratio = (user_persons / floor_persons) if floor_persons > 0 else 0
        meeting_share = round(ff_gas_amount * (sqm_w * m2_ratio + hc_w * person_ratio), 2)

        # Step 1: Distribute remaining gas to ALL first floor companies
        remaining_gas = round(ff_gas_amount - meeting_share, 2)
        ff_gas_shares = _distribute(remaining_gas, ff_gas_eligible,
            ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)

        # Step 2: Distribute meeting room share to user companies only, add to their shares
        if user_companies and meeting_share > 0:
            meeting_user_shares = _distribute(meeting_share, user_companies,
                ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)
            for cid, amt in meeting_user_shares.items():
                ff_gas_shares[cid] = round(ff_gas_shares.get(cid, 0) + amt, 2)
    else:
        # No meeting room — standard distribution
        ff_gas_shares = _distribute(ff_gas_amount, ff_gas_eligible,
            ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)

    # ── NEW COST CATEGORIES ──

    # Consumables (weighted) — uses per-company checkbox
    consumables_amount = monthly_input.get("consumables_total", 0)
    consumables_eligible = [c for c in active if c.get("consumables_eligible", False)]
    cons_ratios = ratios.get("consumables", {"sqm_weight": 50, "headcount_weight": 50})
    consumables_shares = _distribute(consumables_amount, consumables_eligible,
        cons_ratios["sqm_weight"], cons_ratios["headcount_weight"], overrides)

    # Printer (equal split) — uses per-company checkbox
    printer_amount = monthly_input.get("printer_total", 0)
    printer_eligible = [c for c in active if c.get("printer_eligible", False)]
    printer_shares = _equal_split(printer_amount, printer_eligible)

    # Internet (equal split) — uses per-company checkbox
    internet_amount = monthly_input.get("internet_total", 0)
    internet_eligible = [c for c in active if c.get("internet_eligible", False)]
    internet_shares = _equal_split(internet_amount, internet_eligible)

    # Maintenance (fixed EUR per company → RON + 21% VAT)
    VAT_RATE = 0.21
    maintenance_shares = {}
    maintenance_vat_shares = {}
    for c in active:
        maint_eur = c.get("maintenance_rate_eur", 0)
        if maint_eur > 0:
            net = round(maint_eur * eur_rate, 2)
            vat = round(net * VAT_RATE, 2)
            maintenance_shares[c["id"]] = net
            maintenance_vat_shares[c["id"]] = vat

    # ── COMPANY RENT (fixed per company, EUR → RON + 21% VAT) ──
    rent_shares = {}
    rent_vat_shares = {}
    for c in active:
        rent_eur = c.get("monthly_rent_eur", 0)
        if rent_eur > 0:
            net = round(rent_eur * eur_rate, 2)
            vat = round(net * VAT_RATE, 2)
            rent_shares[c["id"]] = net
            rent_vat_shares[c["id"]] = vat

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
            "printer": printer_shares.get(cid, 0.0),
            "internet": internet_shares.get(cid, 0.0),
            "maintenance": maintenance_shares.get(cid, 0.0),
            "maintenance_vat": maintenance_vat_shares.get(cid, 0.0),
            "rent": rent_shares.get(cid, 0.0),
            "rent_vat": rent_vat_shares.get(cid, 0.0),
        }
        r["total"] = round(sum(v for k, v in r.items() if k not in ("company_id", "company_name")), 2)
        results.append(r)

    # ── HOTEL SUBLET POST-PROCESSING ──
    sublet = (settings or {}).get("hotel_sublet", {})
    sublet_pct_raw = sublet.get("percentage", 0)
    # Clamp percentage to safe range [0, 100] to prevent negative customer charges
    if sublet_pct_raw < 0:
        sublet_pct_raw = 0
    if sublet_pct_raw > 100:
        sublet_pct_raw = 100
    if sublet.get("active") and sublet_pct_raw > 0:
        pct = sublet_pct_raw / 100.0
        applies_to = sublet.get("applies_to", [])

        # Find hotel result
        hotel_result = next((r for r in results if r["company_id"] == "hotel"), None)
        if hotel_result:
            sublet_entry = {
                "company_id": "hotel-sublet",
                "company_name": sublet.get("name", "Hotel Sublet"),
            }
            # VAT keys automatically follow their parent cost
            vat_parents = {"maintenance_vat": "maintenance", "rent_vat": "rent"}
            sublet_total = 0.0
            for result_key in ["electricity", "water", "garbage", "gas_hotel", "gas_ground_floor",
                               "gas_first_floor", "consumables", "printer",
                               "internet", "maintenance", "maintenance_vat", "rent", "rent_vat"]:
                # VAT keys follow their parent; other keys check applies_to directly
                parent = vat_parents.get(result_key)
                applies = (parent in applies_to) if parent else (result_key in applies_to)
                if applies and hotel_result.get(result_key, 0) > 0:
                    amount = round(hotel_result[result_key] * pct, 2)
                    sublet_entry[result_key] = amount
                    hotel_result[result_key] = round(hotel_result[result_key] - amount, 2)
                    sublet_total += amount
                else:
                    sublet_entry[result_key] = 0.0

            sublet_entry["total"] = round(sublet_total, 2)
            # Recalculate hotel total — MUST exclude "total" itself or it doubles
            hotel_result["total"] = round(sum(
                v for k, v in hotel_result.items()
                if k not in ("company_id", "company_name", "total")
            ), 2)
            results.append(sublet_entry)

    return results
