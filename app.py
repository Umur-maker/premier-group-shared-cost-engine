import re
import streamlit as st
import tempfile
import os
from datetime import datetime
from data_manager import load_companies, load_settings, save_settings, add_company, update_company
from engine import allocate_costs
from excel_export import generate_excel
from translations import t, floor_name, month_name
from history import save_run, list_runs, get_excel_path, delete_run

st.set_page_config(page_title="Premier Business Center - Shared Cost Engine", layout="centered")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    h1 { font-size: 1.6rem !important; margin-bottom: 0.5rem !important; }
    div[data-testid="stNumberInput"] { margin-bottom: -0.5rem; }
</style>
""", unsafe_allow_html=True)


def _load_data():
    if "companies" not in st.session_state or st.session_state.get("_reload"):
        st.session_state.companies = load_companies()
    if "settings" not in st.session_state or st.session_state.get("_reload"):
        st.session_state.settings = load_settings()
    st.session_state._reload = False

_load_data()

lang_options = {"English": "en", "Romana": "ro"}
lang_label = st.sidebar.selectbox("Language / Limba", list(lang_options.keys()))
lang = lang_options[lang_label]

st.title(t("app_title", lang))

tab1, tab2, tab3, tab4 = st.tabs([
    t("tab_monthly", lang), t("tab_companies", lang),
    t("tab_settings", lang), t("tab_history", lang),
])


def _parse_amount(val):
    v = val.strip().replace(",", ".")
    if not v:
        return 0.0
    f = float(v)
    if f < 0:
        raise ValueError
    return f


def _ron(key):
    """Get translated label with (RON) suffix."""
    return f"{t(key, lang)} (RON)"


# =============================================================================
# TAB 1: Monthly Input
# =============================================================================
with tab1:
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        month = st.selectbox(t("month", lang), range(1, 13),
            index=datetime.now().month - 1,
            format_func=lambda m: month_name(m, lang))
    with col_date2:
        year = st.number_input(t("year", lang), min_value=2020,
            max_value=datetime.now().year + 5, value=datetime.now().year)

    ph = t("input_placeholder", lang)
    eph = t("ext_placeholder", lang)

    st.markdown(f"#### {t('invoice_totals', lang)}")
    col1, col2 = st.columns(2)
    with col1:
        inp_elec = st.text_input(_ron("electricity"), value="", placeholder=ph, key="inp_elec")
        inp_water = st.text_input(_ron("water"), value="", placeholder=ph, key="inp_water")
        inp_garbage = st.text_input(_ron("garbage"), value="", placeholder=ph, key="inp_garbage")
    with col2:
        inp_hgas = st.text_input(_ron("hotel_gas"), value="", placeholder=ph, key="inp_hgas")
        inp_gfgas = st.text_input(_ron("ground_floor_gas"), value="", placeholder=ph, key="inp_gfgas")
        inp_ffgas = st.text_input(_ron("first_floor_gas"), value="", placeholder=ph, key="inp_ffgas")

    st.markdown(f"#### {t('external_usage', lang)}")
    ecol1, ecol2 = st.columns(2)
    with ecol1:
        ext_elec = st.text_input(t("external_electricity", lang), value="", placeholder=eph, key="ext_elec")
        ext_water = st.text_input(t("external_water", lang), value="", placeholder=eph, key="ext_water")
        ext_garbage = st.text_input(t("external_garbage", lang), value="", placeholder=eph, key="ext_garbage")
    with ecol2:
        ext_hgas = st.text_input(t("external_hotel_gas", lang), value="", placeholder=eph, key="ext_hgas")
        ext_gfgas = st.text_input(t("external_gf_gas", lang), value="", placeholder=eph, key="ext_gfgas")
        ext_ffgas = st.text_input(t("external_ff_gas", lang), value="", placeholder=eph, key="ext_ffgas")

    st.divider()

    if st.button(t("generate", lang), type="primary", use_container_width=True):
        field_map = {
            _ron("electricity"): inp_elec,
            _ron("water"): inp_water,
            _ron("garbage"): inp_garbage,
            _ron("hotel_gas"): inp_hgas,
            _ron("ground_floor_gas"): inp_gfgas,
            _ron("first_floor_gas"): inp_ffgas,
            t("external_electricity", lang): ext_elec,
            t("external_water", lang): ext_water,
            t("external_garbage", lang): ext_garbage,
            t("external_hotel_gas", lang): ext_hgas,
            t("external_gf_gas", lang): ext_gfgas,
            t("external_ff_gas", lang): ext_ffgas,
        }

        parsed = {}
        errors = []
        for label, raw in field_map.items():
            try:
                parsed[label] = _parse_amount(raw)
            except (ValueError, AttributeError):
                errors.append(label)

        if errors:
            st.error(t("invalid_number", lang, fields=", ".join(errors)))
        else:
            vals = list(parsed.values())
            monthly_input = {
                "electricity_total": vals[0], "water_total": vals[1], "garbage_total": vals[2],
                "hotel_gas_total": vals[3], "ground_floor_gas_total": vals[4], "first_floor_gas_total": vals[5],
                "external_electricity": vals[6], "external_water": vals[7], "external_garbage": vals[8],
                "external_hotel_gas": vals[9], "external_gf_gas": vals[10], "external_ff_gas": vals[11],
            }

            active_companies = [c for c in st.session_state.companies if c["active"]]
            if not active_companies:
                st.error(t("no_active", lang))
            else:
                checks = [
                    ("electricity_total", "external_electricity", t("electricity", lang)),
                    ("water_total", "external_water", t("water", lang)),
                    ("garbage_total", "external_garbage", t("garbage", lang)),
                    ("hotel_gas_total", "external_hotel_gas", t("hotel_gas", lang)),
                    ("ground_floor_gas_total", "external_gf_gas", t("ground_floor_gas", lang)),
                    ("first_floor_gas_total", "external_ff_gas", t("first_floor_gas", lang)),
                ]
                has_error = False
                for total_key, ext_key, field_label in checks:
                    if monthly_input[ext_key] > monthly_input[total_key]:
                        st.error(t("external_exceeds", lang, field=field_label,
                                   ext=monthly_input[ext_key], total=monthly_input[total_key]))
                        has_error = True

                if not has_error:
                    settings = st.session_state.settings
                    results = allocate_costs(st.session_state.companies, settings["ratios"], monthly_input)

                    if not results:
                        st.warning(t("no_results", lang))
                    else:
                        st.markdown(f"#### {t('preview', lang)}")
                        preview_cols = [
                            (t("excel_company", lang), "company_name", False),
                            (t("electricity", lang)[:4], "electricity", True),
                            (t("water", lang)[:4], "water", True),
                            (t("garbage", lang)[:4], "garbage", True),
                            ("Gas(H)", "gas_hotel", True),
                            ("Gas(GF)", "gas_ground_floor", True),
                            ("Gas(1F)", "gas_first_floor", True),
                            (t("excel_total", lang) + " RON", "total", True),
                        ]
                        hcols = st.columns([2.5] + [1] * 7)
                        for i, (lbl, _, _) in enumerate(preview_cols):
                            hcols[i].markdown(f"**{lbl}**")
                        for r in results:
                            rcols = st.columns([2.5] + [1] * 7)
                            for i, (_, key, is_num) in enumerate(preview_cols):
                                val = r[key]
                                rcols[i].write(f"{val:,.2f} RON" if is_num else val)

                        mn = month_name(month, lang)
                        filename = f"Premier_BC_Cost_Allocation_{year}_{month:02d}_{mn}.xlsx"
                        tmp_path = os.path.join(tempfile.gettempdir(), filename)

                        generate_excel(tmp_path, results, monthly_input,
                                       settings["ratios"], active_companies, lang)

                        save_run(month, year, lang, monthly_input,
                                 settings["ratios"], st.session_state.companies,
                                 results, tmp_path)

                        with open(tmp_path, "rb") as f:
                            st.download_button(
                                label=f"{t('download', lang)} {filename}",
                                data=f, file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary", use_container_width=True)

# =============================================================================
# TAB 2: Companies - Add New first, then list
# =============================================================================
with tab2:
    companies = st.session_state.companies
    floor_opts = ["ground_floor", "first_floor", "mezzanine", "hotel"]
    floor_labels = [floor_name(f, lang) for f in floor_opts]

    # --- Add New Company (top) ---
    st.markdown(f"#### {t('add_company', lang)}")
    with st.form("add_company_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            add_name = st.text_input(t("company_name", lang))
            add_area = st.number_input(t("area_m2", lang), min_value=0.0, step=0.01)
            add_hc = st.number_input(t("persons", lang), min_value=0, step=1, value=1)
        with col2:
            add_floor_idx = st.selectbox(t("floor", lang), range(len(floor_opts)),
                format_func=lambda i: floor_labels[i])
            add_floor = floor_opts[add_floor_idx]
            add_building = st.text_input(t("building", lang), value="C4")
            add_heating = st.checkbox(t("has_heating", lang), value=True)
        with col3:
            add_elec = st.checkbox(t("electricity", lang), value=True)
            add_water = st.checkbox(t("water", lang), value=True)
            add_garbage = st.checkbox(t("garbage", lang), value=True)

        submitted = st.form_submit_button(t("add_company", lang), type="primary")
        if submitted:
            existing_names = [x["name"].strip().lower() for x in companies]
            existing_ids = [x["id"] for x in companies]
            company_id = re.sub(r"[^a-z0-9]+", "-", add_name.strip().lower()).strip("-")

            if not add_name.strip():
                st.error(t("name_empty", lang))
            elif add_name.strip().lower() in existing_names:
                st.error(t("name_exists", lang, name=add_name))
            elif company_id in existing_ids:
                st.error(t("id_exists", lang))
            elif add_area <= 0:
                st.error(t("area_zero", lang))
            else:
                add_company({
                    "id": company_id, "name": add_name.strip(), "area_m2": add_area,
                    "headcount_default": add_hc, "building": add_building, "floor": add_floor,
                    "has_heating": add_heating, "electricity_eligible": add_elec,
                    "water_eligible": add_water, "garbage_eligible": add_garbage, "active": True,
                })
                st.session_state._reload = True
                st.success(t("added_ok", lang, name=add_name))
                st.rerun()

    st.divider()

    # --- Company List ---
    for idx, c in enumerate(companies, 1):
        icon = "🟢" if c["active"] else "🔴"
        label = f'{t("company_no", lang)} {idx} {icon} {c["name"]} \u2014 {c["area_m2"]} m\u00b2, {c["headcount_default"]} {t("excel_persons", lang).lower()}, {floor_name(c["floor"], lang)}'

        with st.expander(label):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_name = st.text_input(t("company_name", lang), value=c["name"], key=f"ed_name_{c['id']}")
                new_area = st.number_input(t("area_m2", lang), value=c["area_m2"], key=f"ed_area_{c['id']}", step=0.01)
                new_hc = st.number_input(t("persons", lang), value=c["headcount_default"], min_value=0, key=f"ed_hc_{c['id']}", step=1)
            with col2:
                new_floor_idx = st.selectbox(t("floor", lang), range(len(floor_opts)),
                    index=floor_opts.index(c["floor"]),
                    format_func=lambda i: floor_labels[i], key=f"ed_floor_{c['id']}")
                new_floor = floor_opts[new_floor_idx]
                new_building = st.text_input(t("building", lang), value=c["building"], key=f"ed_bld_{c['id']}")
                new_heating = st.checkbox(t("has_heating", lang), value=c["has_heating"], key=f"ed_heat_{c['id']}")
            with col3:
                new_elec = st.checkbox(t("electricity", lang), value=c["electricity_eligible"], key=f"ed_elec_{c['id']}")
                new_water = st.checkbox(t("water", lang), value=c["water_eligible"], key=f"ed_water_{c['id']}")
                new_garbage = st.checkbox(t("garbage", lang), value=c["garbage_eligible"], key=f"ed_garb_{c['id']}")
                new_active = st.checkbox(t("active", lang), value=c["active"], key=f"ed_act_{c['id']}")

            if st.button(t("save", lang), key=f"save_{c['id']}"):
                other_names = [x["name"].strip().lower() for x in companies if x["id"] != c["id"]]
                if new_name.strip().lower() in other_names:
                    st.error(t("name_exists", lang, name=new_name))
                elif not new_name.strip():
                    st.error(t("name_empty", lang))
                elif new_area <= 0:
                    st.error(t("area_zero", lang))
                elif new_hc < 0:
                    st.error(t("persons_negative", lang))
                else:
                    update_company(c["id"], {
                        "name": new_name.strip(), "area_m2": new_area,
                        "headcount_default": new_hc, "floor": new_floor,
                        "building": new_building, "has_heating": new_heating,
                        "electricity_eligible": new_elec, "water_eligible": new_water,
                        "garbage_eligible": new_garbage, "active": new_active,
                    })
                    st.session_state._reload = True
                    st.success(t("saved_ok", lang, name=new_name))
                    st.rerun()

# =============================================================================
# TAB 3: Settings
# =============================================================================
with tab3:
    saved_settings = st.session_state.settings

    st.markdown(f"#### {t('ratios_title', lang)}")
    st.caption(t("ratios_help", lang))

    pending_ratios = {}
    settings_changed = False

    for expense_type in ["electricity", "gas", "water", "garbage"]:
        current = saved_settings["ratios"][expense_type]
        col1, col2 = st.columns(2)
        with col1:
            new_sqm = st.number_input(
                t("sqm_pct", lang, type=expense_type.capitalize()),
                min_value=0, max_value=100, value=current["sqm_weight"],
                step=5, key=f"ratio_sqm_{expense_type}")
        with col2:
            st.caption(t("person_pct", lang, type=expense_type.capitalize()))
            st.markdown(f"&nbsp; **{100 - new_sqm}%**")

        pending_ratios[expense_type] = {"sqm_weight": new_sqm, "headcount_weight": 100 - new_sqm}
        if new_sqm != current["sqm_weight"]:
            settings_changed = True

    if settings_changed:
        st.warning(t("unsaved_warning", lang))
        if st.button(t("save_settings", lang), type="primary"):
            saved_settings["ratios"] = pending_ratios
            save_settings(saved_settings)
            st.session_state._reload = True
            st.success(t("settings_saved", lang))
            st.rerun()

# =============================================================================
# TAB 4: History
# =============================================================================
with tab4:
    st.markdown(f"#### {t('history_title', lang)}")
    runs = list_runs()

    if not runs:
        st.info(t("history_empty", lang))
    else:
        for entry in runs:
            mn = month_name(entry["month"], entry.get("language", "en"))
            run_label = t("history_run", lang, month=mn, year=entry["year"])
            gen_date = entry["generated_at"][:10]

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{run_label}** &nbsp; ({t('history_generated', lang, date=gen_date)})")
            with col2:
                excel_path = get_excel_path(entry)
                if os.path.exists(excel_path):
                    with open(excel_path, "rb") as f:
                        st.download_button(
                            t("history_download", lang), data=f,
                            file_name=os.path.basename(excel_path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{entry['id']}")
            with col3:
                if st.button(t("history_delete", lang), key=f"del_{entry['id']}"):
                    delete_run(entry["id"])
                    st.success(t("history_deleted", lang))
                    st.rerun()
