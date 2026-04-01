import re
import streamlit as st
import tempfile
import os
from datetime import datetime
from data_manager import (
    load_companies, load_settings, save_settings,
    add_company, update_company,
)
from engine import allocate_costs
from excel_export import generate_excel

st.set_page_config(page_title="Premier Group - Shared Cost Engine", layout="centered")

# --- Custom CSS for compact layout ---
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    h1 { font-size: 1.6rem !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.05rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    div[data-testid="stNumberInput"] { margin-bottom: -0.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("Premier Group - Shared Cost Engine")


def _load_data():
    if "companies" not in st.session_state or st.session_state.get("_reload"):
        st.session_state.companies = load_companies()
    if "settings" not in st.session_state or st.session_state.get("_reload"):
        st.session_state.settings = load_settings()
    st.session_state._reload = False


_load_data()

tab1, tab2, tab3 = st.tabs(["Monthly Input", "Companies", "Settings"])

# =============================================================================
# TAB 1: Monthly Input
# =============================================================================
with tab1:
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        month = st.selectbox(
            "Month", range(1, 13),
            index=datetime.now().month - 1,
            format_func=lambda m: datetime(2000, m, 1).strftime("%B"),
        )
    with col_date2:
        year = st.number_input("Year", min_value=2020, max_value=datetime.now().year + 5, value=datetime.now().year)

    st.markdown("#### Invoice Totals (RON)")
    col1, col2 = st.columns(2)
    with col1:
        electricity_total = st.text_input("Electricity", value="", key="inp_elec", placeholder="e.g. 3598.89")
        water_total = st.text_input("Water", value="", key="inp_water", placeholder="e.g. 855.60")
        garbage_total = st.text_input("Garbage", value="", key="inp_garbage", placeholder="e.g. 407.74")
    with col2:
        hotel_gas_total = st.text_input("Hotel Gas", value="", key="inp_hgas", placeholder="e.g. 4021.74")
        ground_floor_gas_total = st.text_input("Ground Floor Gas", value="", key="inp_gfgas", placeholder="e.g. 2583.53")
        first_floor_gas_total = st.text_input("First Floor Gas", value="", key="inp_ffgas", placeholder="e.g. 3172.14")

    st.markdown("#### Adjustments (RON)")
    adj1, adj2 = st.columns(2)
    with adj1:
        external_water = st.text_input("External Water Deduction", value="", key="inp_ext_water", placeholder="0")
    with adj2:
        external_electricity = st.text_input("External Electricity Contribution", value="", key="inp_ext_elec", placeholder="0")

    st.divider()

    if st.button("Generate Excel Report", type="primary", use_container_width=True):
        # Parse text inputs to floats
        def _parse(val, label):
            v = val.strip().replace(",", ".")
            if not v:
                return 0.0
            try:
                f = float(v)
                if f < 0:
                    raise ValueError
                return f
            except ValueError:
                return label  # return label as error marker

        fields = {
            "Electricity": electricity_total,
            "Water": water_total,
            "Garbage": garbage_total,
            "Hotel Gas": hotel_gas_total,
            "Ground Floor Gas": ground_floor_gas_total,
            "First Floor Gas": first_floor_gas_total,
            "External Water Deduction": external_water,
            "External Electricity Contribution": external_electricity,
        }

        parsed = {}
        parse_errors = []
        for label, raw in fields.items():
            result = _parse(raw, label)
            if isinstance(result, str):
                parse_errors.append(label)
            else:
                parsed[label] = result

        if parse_errors:
            st.error(f"Invalid number in: {', '.join(parse_errors)}. Use digits and decimal point only.")
        else:
            p = parsed
            active_companies = [c for c in st.session_state.companies if c["active"]]

            has_error = False
            if p["External Water Deduction"] > p["Water"]:
                st.error(f"External water deduction ({p['External Water Deduction']:.2f}) cannot exceed water total ({p['Water']:.2f}).")
                has_error = True
            if p["External Electricity Contribution"] > p["Electricity"]:
                st.error(f"External electricity contribution ({p['External Electricity Contribution']:.2f}) cannot exceed electricity total ({p['Electricity']:.2f}).")
                has_error = True
            if not active_companies:
                st.error("No active companies. Go to Companies tab to activate at least one.")
                has_error = True

            if not has_error:
                monthly_input = {
                    "electricity_total": p["Electricity"],
                    "garbage_total": p["Garbage"],
                    "water_total": p["Water"],
                    "hotel_gas_total": p["Hotel Gas"],
                    "ground_floor_gas_total": p["Ground Floor Gas"],
                    "first_floor_gas_total": p["First Floor Gas"],
                    "external_water_deduction": p["External Water Deduction"],
                    "external_electricity_contribution": p["External Electricity Contribution"],
                }

                settings = st.session_state.settings
                results = allocate_costs(
                    st.session_state.companies,
                    settings["ratios"],
                    monthly_input,
                )

                if not results:
                    st.warning("No allocatable results. All companies may be inactive or ineligible.")
                else:
                    # Preview table
                    st.markdown("#### Allocation Preview")
                    preview_cols = [
                        ("Company", "company_name", False),
                        ("Elec.", "electricity", True),
                        ("Water", "water", True),
                        ("Garb.", "garbage", True),
                        ("Gas(H)", "gas_hotel", True),
                        ("Gas(GF)", "gas_ground_floor", True),
                        ("Gas(1F)", "gas_first_floor", True),
                        ("Total", "total", True),
                    ]
                    header_cols = st.columns([2.5] + [1] * 7)
                    for i, (label, _, _) in enumerate(preview_cols):
                        header_cols[i].markdown(f"**{label}**")
                    for r in results:
                        row_cols = st.columns([2.5] + [1] * 7)
                        for i, (_, key, is_num) in enumerate(preview_cols):
                            val = r[key]
                            row_cols[i].write(f"{val:,.2f}" if is_num else val)

                    # Generate Excel
                    month_name = datetime(2000, month, 1).strftime("%B")
                    filename = f"Premier_Group_Cost_Allocation_{year}_{month:02d}_{month_name}.xlsx"
                    tmp_path = os.path.join(tempfile.gettempdir(), filename)

                    generate_excel(
                        tmp_path, results, monthly_input,
                        settings["ratios"], active_companies,
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
    companies = st.session_state.companies

    for c in companies:
        icon = "🟢" if c["active"] else "🔴"
        label = f'{icon} {c["name"]} — {c["area_m2"]} m\u00b2, {c["headcount_default"]} people, {c["floor"].replace("_", " ").title()}'

        with st.expander(label):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("Name", value=c["name"], key=f"ed_name_{c['id']}")
                new_area = st.number_input("Area (m\u00b2)", value=c["area_m2"], key=f"ed_area_{c['id']}", step=0.01)
                new_hc = st.number_input("Headcount", value=c["headcount_default"], min_value=0, key=f"ed_hc_{c['id']}", step=1)
            with col2:
                floor_opts = ["ground_floor", "first_floor", "mezzanine", "hotel"]
                new_floor = st.selectbox("Floor", floor_opts, index=floor_opts.index(c["floor"]), key=f"ed_floor_{c['id']}")
                new_building = st.text_input("Building", value=c["building"], key=f"ed_bld_{c['id']}")
                new_heating = st.checkbox("Has Heating (Gas)", value=c["has_heating"], key=f"ed_heat_{c['id']}")
            with col3:
                new_elec = st.checkbox("Electricity", value=c["electricity_eligible"], key=f"ed_elec_{c['id']}")
                new_water = st.checkbox("Water", value=c["water_eligible"], key=f"ed_water_{c['id']}")
                new_garbage = st.checkbox("Garbage", value=c["garbage_eligible"], key=f"ed_garb_{c['id']}")
                new_active = st.checkbox("Active", value=c["active"], key=f"ed_act_{c['id']}")

            if st.button("Save", key=f"save_{c['id']}"):
                other_names = [x["name"].strip().lower() for x in companies if x["id"] != c["id"]]
                if new_name.strip().lower() in other_names:
                    st.error(f"Company name '{new_name}' already exists.")
                elif not new_name.strip():
                    st.error("Company name cannot be empty.")
                elif new_area <= 0:
                    st.error("Area must be greater than 0.")
                elif new_hc < 0:
                    st.error("Headcount cannot be negative.")
                else:
                    update_company(c["id"], {
                        "name": new_name.strip(),
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
                    st.session_state._reload = True
                    st.success(f"'{new_name}' saved successfully.")
                    st.rerun()

    st.divider()
    st.markdown("#### Add New Company")
    with st.form("add_company_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            add_name = st.text_input("Company Name")
            add_area = st.number_input("Area (m\u00b2)", min_value=0.0, step=0.01)
            add_hc = st.number_input("Headcount", min_value=0, step=1, value=1)
        with col2:
            add_floor = st.selectbox("Floor", ["ground_floor", "first_floor", "mezzanine", "hotel"])
            add_building = st.text_input("Building", value="C4")
            add_heating = st.checkbox("Has Heating (Gas)", value=True)
        with col3:
            add_elec = st.checkbox("Electricity", value=True)
            add_water = st.checkbox("Water", value=True)
            add_garbage = st.checkbox("Garbage", value=True)

        submitted = st.form_submit_button("Add Company", type="primary")
        if submitted:
            existing_names = [x["name"].strip().lower() for x in companies]
            existing_ids = [x["id"] for x in companies]
            company_id = re.sub(r"[^a-z0-9]+", "-", add_name.strip().lower()).strip("-")

            if not add_name.strip():
                st.error("Company name is required.")
            elif add_name.strip().lower() in existing_names:
                st.error(f"Company name '{add_name}' already exists.")
            elif company_id in existing_ids:
                st.error(f"A company with this ID already exists. Choose a different name.")
            elif add_area <= 0:
                st.error("Area must be greater than 0.")
            else:
                new_company = {
                    "id": company_id,
                    "name": add_name.strip(),
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
                st.session_state._reload = True
                st.success(f"'{add_name}' added successfully.")
                st.rerun()

# =============================================================================
# TAB 3: Settings
# =============================================================================
with tab3:
    saved_settings = st.session_state.settings

    st.markdown("#### Allocation Ratios")
    st.caption("sqm % + headcount % must equal 100 for each expense type.")

    pending_ratios = {}
    settings_changed = False
    ratio_errors = []

    for expense_type in ["electricity", "gas", "water", "garbage"]:
        current = saved_settings["ratios"][expense_type]
        col1, col2 = st.columns(2)
        with col1:
            new_sqm = st.number_input(
                f"{expense_type.capitalize()} — sqm %",
                min_value=0, max_value=100,
                value=current["sqm_weight"],
                step=5,
                key=f"ratio_sqm_{expense_type}",
            )
        with col2:
            new_hc = st.number_input(
                f"{expense_type.capitalize()} — headcount %",
                min_value=0, max_value=100,
                value=current["headcount_weight"],
                step=5,
                key=f"ratio_hc_{expense_type}",
            )

        if new_sqm + new_hc != 100:
            ratio_errors.append(expense_type.capitalize())

        pending_ratios[expense_type] = {
            "sqm_weight": new_sqm,
            "headcount_weight": new_hc,
        }
        if new_sqm != current["sqm_weight"] or new_hc != current["headcount_weight"]:
            settings_changed = True

    if ratio_errors:
        st.error(f"sqm % + headcount % must equal 100 for: {', '.join(ratio_errors)}")

    if settings_changed and not ratio_errors:
        if st.button("Save Settings", type="primary"):
            saved_settings["ratios"] = pending_ratios
            save_settings(saved_settings)
            st.session_state._reload = True
            st.success("Settings saved successfully.")
            st.rerun()
