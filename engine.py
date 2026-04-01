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

    # Rebalance weights if one dimension is zero
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


def _net_amount(total, external):
    """Calculate net amount after external usage. Raises ValueError if negative."""
    net = total - external
    if net < 0:
        raise ValueError(f"Net amount is negative ({net:.2f}). External usage exceeds total.")
    return net


def allocate_costs(companies, ratios, monthly_input, headcount_overrides=None):
    """Main allocation function. Pure function: no I/O, no side effects.

    monthly_input fields:
        electricity_total, garbage_total, water_total,
        hotel_gas_total, ground_floor_gas_total, first_floor_gas_total,
        external_electricity, external_water, external_garbage,
        external_hotel_gas, external_gf_gas, external_ff_gas

    Also supports legacy field names (external_water_deduction, external_electricity_contribution).
    """
    active = [c for c in companies if c["active"]]
    overrides = headcount_overrides or {}

    def _ext(key, legacy_key=None):
        val = monthly_input.get(key, 0)
        if val == 0 and legacy_key:
            val = monthly_input.get(legacy_key, 0)
        return val

    # Electricity
    elec_eligible = [c for c in active if c["electricity_eligible"]]
    elec_amount = _net_amount(
        monthly_input["electricity_total"],
        _ext("external_electricity", "external_electricity_contribution"),
    )
    elec_shares = _distribute(elec_amount, elec_eligible,
        ratios["electricity"]["sqm_weight"], ratios["electricity"]["headcount_weight"], overrides)

    # Water
    water_eligible = [c for c in active if c["water_eligible"]]
    water_amount = _net_amount(
        monthly_input["water_total"],
        _ext("external_water", "external_water_deduction"),
    )
    water_shares = _distribute(water_amount, water_eligible,
        ratios["water"]["sqm_weight"], ratios["water"]["headcount_weight"], overrides)

    # Garbage
    garbage_eligible = [c for c in active if c["garbage_eligible"]]
    garbage_amount = _net_amount(
        monthly_input["garbage_total"],
        _ext("external_garbage"),
    )
    garbage_shares = _distribute(garbage_amount, garbage_eligible,
        ratios["garbage"]["sqm_weight"], ratios["garbage"]["headcount_weight"], overrides)

    # Gas Hotel
    hotel_gas_eligible = [c for c in active if c["floor"] == "hotel" and c["has_heating"]]
    hotel_gas_amount = _net_amount(
        monthly_input["hotel_gas_total"],
        _ext("external_hotel_gas"),
    )
    hotel_gas_shares = _distribute(hotel_gas_amount, hotel_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)

    # Gas Ground Floor
    gf_gas_eligible = [c for c in active if c["floor"] == "ground_floor" and c["has_heating"]]
    gf_gas_amount = _net_amount(
        monthly_input["ground_floor_gas_total"],
        _ext("external_gf_gas"),
    )
    gf_gas_shares = _distribute(gf_gas_amount, gf_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)

    # Gas First Floor
    ff_gas_eligible = [c for c in active if c["floor"] == "first_floor" and c["has_heating"]]
    ff_gas_amount = _net_amount(
        monthly_input["first_floor_gas_total"],
        _ext("external_ff_gas"),
    )
    ff_gas_shares = _distribute(ff_gas_amount, ff_gas_eligible,
        ratios["gas"]["sqm_weight"], ratios["gas"]["headcount_weight"], overrides)

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
        total = round(electricity + water + garbage + gas_hotel + gas_gf + gas_ff, 2)

        results.append({
            "company_id": cid,
            "company_name": c["name"],
            "electricity": electricity,
            "water": water,
            "garbage": garbage,
            "gas_hotel": gas_hotel,
            "gas_ground_floor": gas_gf,
            "gas_first_floor": gas_ff,
            "total": total,
        })

    return results
