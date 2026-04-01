import re
import streamlit as st
import tempfile
import os
import pandas as pd
from datetime import datetime
from data_manager import (
    load_companies, save_companies, load_settings, save_settings,
    add_company, update_company,
)
from engine import allocate_costs
from excel_export import generate_excel


st.set_page_config(page_title="Premier Group - Shared Cost Engine", layout="wide")
st.title("Premier Group - Shared Cost Engine")


def _load_data():
    if "companies" not in st.session_state or st.session_state.get("_reload"):
        st.session_state.companies = load_companies()
    if "settings" not in st.session_state or st.session_state.get("_reload"):
        st.session_state.settings = load_settings()
    st.session_state._reload = False


_load_data()

tab1, tab2, tab3 = st.tabs(["Monthly Input", "Company Management", "Settings"])

# =============================================================================
# TAB 1: Monthly Input
# =============================================================================
with tab1:
    st.header("Monthly Cost Allocation")

    col_date1, col_date2 = st.columns(2)
    with col_date1:
        month = st.selectbox(
            "Month", range(1, 13),
            index=datetime.now().month - 1,
            format_func=lambda m: datetime(2000, m, 1).strftime("%B"),
        )
    with col_date2:
        year = st.number_input("Year", min_value=2020, max_value=datetime.now().year + 5, value=datetime.now().year)

    st.subheader("Invoice Totals (RON)")
    col1, col2, col3 = st.columns(3)
    with col1:
        electricity_total = st.number_input(
            "Electricity Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        water_total = st.number_input(
            "Water Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    with col2:
        garbage_total = st.number_input(
            "Garbage Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        hotel_gas_total = st.number_input(
            "Hotel Gas Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    with col3:
        ground_floor_gas_total = st.number_input(
            "Ground Floor Gas Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")
        first_floor_gas_total = st.number_input(
            "First Floor Gas Total", min_value=0.0, value=0.0, step=0.01, format="%.2f")

    st.subheader("Adjustments (RON)")
    adj1, adj2 = st.columns(2)
    with adj1:
        external_water = st.number_input(
            "External Water Deduction", min_value=0.0, value=0.0, step=0.01, format="%.2f")
    with adj2:
        external_electricity = st.number_input(
            "External Electricity Contribution", min_value=0.0, value=0.0, step=0.01, format="%.2f")

    # Headcount overrides - use session state companies (same source as engine)
    st.subheader("Headcount (this month)")
    active_companies = [c for c in st.session_state.companies if c["active"]]
    headcount_overrides = {}
    cols = st.columns(4)
    for i, c in enumerate(active_companies):
        with cols[i % 4]:
            hc = st.number_input(
                c["name"], min_value=0, value=c["headcount_default"],
                step=1, key=f"hc_{c['id']}",
            )
            if hc != c["headcount_default"]:
                headcount_overrides[c["id"]] = hc

    st.divider()

    if st.button("Generate Excel Report", type="primary", use_container_width=True):
        # Validation
        has_error = False
        if external_water > water_total:
            st.error(f"External water deduction ({external_water:.2f}) cannot exceed water total ({water_total:.2f}).")
            has_error = True
        if external_electricity > electricity_total:
            st.error(f"External electricity contribution ({external_electricity:.2f}) cannot exceed electricity total ({electricity_total:.2f}).")
            has_error = True
        if not active_companies:
            st.error("No active companies found. Go to Company Management to activate at least one company.")
            has_error = True

        if not has_error:
            monthly_input = {
                "electricity_total": electricity_total,
                "garbage_total": garbage_total,
                "water_total": water_total,
                "hotel_gas_total": hotel_gas_total,
                "ground_floor_gas_total": ground_floor_gas_total,
                "first_floor_gas_total": first_floor_gas_total,
                "external_water_deduction": external_water,
                "external_electricity_contribution": external_electricity,
            }

            settings = st.session_state.settings
            hc_overrides = headcount_overrides if headcount_overrides else None
            results = allocate_costs(
                st.session_state.companies,
                settings["ratios"],
                monthly_input,
                settings["defaults"],
                hc_overrides,
            )

            if not results:
                st.warning("No allocatable results. All companies may be inactive or ineligible.")
            else:
                # Check if all headcounts are zero (allocation fell back to sqm-only)
                effective_hcs = [
                    (hc_overrides or {}).get(c["id"], c["headcount_default"])
                    for c in active_companies
                ]
                if all(h == 0 for h in effective_hcs):
                    st.info("All headcounts are 0 this month. Allocation is based on area (sqm) only.")

                # Preview table
                st.subheader("Allocation Preview")
                df = pd.DataFrame(results)
                df = df.rename(columns={
                    "company_name": "Company",
                    "electricity": "Electricity",
                    "water": "Water",
                    "garbage": "Garbage",
                    "gas_hotel": "Gas (Hotel)",
                    "gas_ground_floor": "Gas (GF)",
                    "gas_first_floor": "Gas (1F)",
                    "total": "Total",
                })
                display_cols = ["Company", "Electricity", "Water", "Garbage",
                                "Gas (Hotel)", "Gas (GF)", "Gas (1F)", "Total"]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

                # Generate Excel
                month_name = datetime(2000, month, 1).strftime("%B")
                filename = f"Premier_Group_Cost_Allocation_{year}_{month:02d}_{month_name}.xlsx"
                tmp_path = os.path.join(tempfile.gettempdir(), filename)

                generate_excel(
                    tmp_path, results, monthly_input,
                    settings["ratios"], active_companies, settings["defaults"],
                    hc_overrides,
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
    st.header("Company Management")
    companies = st.session_state.companies

    st.subheader("Current Companies")
    for c in companies:
        icon = "🟢" if c["active"] else "🔴"
        label = f'{icon} {c["name"]} - {c["floor"].replace("_", " ").title()} - {c["area_m2"]} m2'

        with st.expander(label):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input("Name", value=c["name"], key=f"ed_name_{c['id']}")
                new_area = st.number_input("Area (m2)", value=c["area_m2"], key=f"ed_area_{c['id']}", step=0.01)
                new_hc = st.number_input("Default Headcount", value=c["headcount_default"], min_value=0, key=f"ed_hc_{c['id']}", step=1)
            with col2:
                floor_opts = ["ground_floor", "first_floor", "mezzanine", "hotel"]
                new_floor = st.selectbox("Floor", floor_opts, index=floor_opts.index(c["floor"]), key=f"ed_floor_{c['id']}")
                new_building = st.text_input("Building", value=c["building"], key=f"ed_bld_{c['id']}")
                new_heating = st.checkbox("Has Heating (Gas)", value=c["has_heating"], key=f"ed_heat_{c['id']}")
            with col3:
                new_elec = st.checkbox("Electricity Eligible", value=c["electricity_eligible"], key=f"ed_elec_{c['id']}")
                new_water = st.checkbox("Water Eligible", value=c["water_eligible"], key=f"ed_water_{c['id']}")
                new_garbage = st.checkbox("Garbage Eligible", value=c["garbage_eligible"], key=f"ed_garb_{c['id']}")
                new_active = st.checkbox("Active", value=c["active"], key=f"ed_act_{c['id']}")

            if st.button("Save Changes", key=f"save_{c['id']}"):
                other_names = [x["name"].strip().lower() for x in companies if x["id"] != c["id"]]
                if new_name.strip().lower() in other_names:
                    st.error(f"Company name '{new_name}' already exists.")
                elif not new_name.strip():
                    st.error("Company name cannot be empty.")
                elif new_area <= 0:
                    st.error("Area must be greater than 0.")
                elif new_hc < 0:
                    st.error("Default headcount cannot be negative.")
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
                    st.success(f"Updated {new_name}")
                    st.rerun()

    # Add new company
    st.divider()
    st.subheader("Add New Company")
    with st.form("add_company_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            add_name = st.text_input("Company Name")
            add_area = st.number_input("Area (m2)", min_value=0.0, step=0.01)
            add_hc = st.number_input("Default Headcount", min_value=0, step=1, value=1)
        with col2:
            add_floor = st.selectbox("Floor", ["ground_floor", "first_floor", "mezzanine", "hotel"])
            add_building = st.text_input("Building", value="C4")
            add_heating = st.checkbox("Has Heating (Gas)", value=True)
        with col3:
            add_elec = st.checkbox("Electricity Eligible", value=True)
            add_water = st.checkbox("Water Eligible", value=True)
            add_garbage = st.checkbox("Garbage Eligible", value=True)

        submitted = st.form_submit_button("Add Company", type="primary")
        if submitted:
            existing_names = [x["name"].strip().lower() for x in companies]
            existing_ids = [x["id"] for x in companies]
            # Safe ID: lowercase, replace non-alphanumeric with dash, collapse
            company_id = re.sub(r"[^a-z0-9]+", "-", add_name.strip().lower()).strip("-")

            if not add_name.strip():
                st.error("Company name is required.")
            elif add_name.strip().lower() in existing_names:
                st.error(f"Company name '{add_name}' already exists.")
            elif company_id in existing_ids:
                st.error(f"Company ID '{company_id}' already exists. Choose a different name.")
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
                st.success(f"Added {add_name}")
                st.rerun()

# =============================================================================
# TAB 3: Settings
# =============================================================================
with tab3:
    st.header("Settings")
    saved_settings = st.session_state.settings

    st.subheader("Allocation Ratios")
    st.caption("Drag the slider to set sqm weight. Headcount weight adjusts automatically to total 100%.")

    # Use temporary UI values - do NOT mutate saved_settings until Save
    pending_ratios = {}
    settings_changed = False

    for expense_type in ["electricity", "gas", "water", "garbage"]:
        current = saved_settings["ratios"][expense_type]
        col1, col2 = st.columns([3, 1])
        with col1:
            new_sqm = st.slider(
                f"{expense_type.capitalize()} - sqm %",
                min_value=0, max_value=100,
                value=current["sqm_weight"],
                key=f"ratio_{expense_type}",
            )
        with col2:
            st.metric("headcount %", f"{100 - new_sqm}%")

        pending_ratios[expense_type] = {
            "sqm_weight": new_sqm,
            "headcount_weight": 100 - new_sqm,
        }
        if new_sqm != current["sqm_weight"]:
            settings_changed = True

    st.divider()
    st.subheader("Default Values")
    new_elevator = st.number_input(
        "Elevator Cost (RON) - this value is not added to any bill, it is shown for reference only",
        min_value=0.0,
        value=float(saved_settings["defaults"]["elevator_cost"]),
        step=10.0,
        format="%.2f",
    )
    if new_elevator != saved_settings["defaults"]["elevator_cost"]:
        settings_changed = True

    if settings_changed:
        if st.button("Save Settings", type="primary"):
            saved_settings["ratios"] = pending_ratios
            saved_settings["defaults"]["elevator_cost"] = new_elevator
            save_settings(saved_settings)
            st.session_state._reload = True
            st.success("Settings saved successfully!")
            st.rerun()
