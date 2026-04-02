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
from formatting import format_ron, parse_ron_input

st.set_page_config(
    page_title="Premier Business Center",
    layout="wide",
    initial_sidebar_state="expanded",
)

OPTIONAL_FIELDS = ["office_location", "contact_person", "phone", "email",
                    "beginning_date", "expiration_date", "notes"]
FLOOR_OPTS = ["ground_floor", "first_floor", "mezzanine", "hotel"]


def _load_data():
    if "companies" not in st.session_state or st.session_state.get("_reload"):
        st.session_state.companies = load_companies()
    if "settings" not in st.session_state or st.session_state.get("_reload"):
        st.session_state.settings = load_settings()
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    st.session_state._reload = False

_load_data()
lang = st.session_state.lang
is_dark = st.session_state.theme == "dark"

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Premier Business Center")
    st.caption("Shared Cost Engine")
    st.divider()
    nav_items = {
        t("nav_monthly", lang): "monthly",
        t("nav_companies", lang): "companies",
        t("nav_settings", lang): "settings",
        t("nav_history", lang): "history",
    }
    if "page" not in st.session_state:
        st.session_state.page = "monthly"
    for label, pid in nav_items.items():
        bt = "primary" if st.session_state.page == pid else "secondary"
        if st.button(label, key=f"nav_{pid}", use_container_width=True, type=bt):
            st.session_state.page = pid
            st.rerun()

page = st.session_state.page

# --- Theme ---
if is_dark:
    st.markdown("""<style>
    .stApp { background: #0d1117; color: #e6edf3; }
    section[data-testid="stSidebar"] { background: #161b22; }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stCaption p { color: #c9d1d9 !important; }
    h1, h2, h3, h4, h5 { color: #f0f3f6 !important; }
    label, .stCaption p { color: #c9d1d9 !important; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea {
        background: #0d1117 !important; color: #e6edf3 !important; border-color: #30363d !important;
    }
    .stTextInput>div>div>input::placeholder { color: #6e7681 !important; }
    .stSelectbox>div>div { background: #0d1117; color: #e6edf3; }
    div[data-testid="stExpander"] { border-color: #30363d; background: #161b22; }
    div[data-testid="stExpander"] summary span { color: #e6edf3 !important; }
    div[data-testid="stForm"] { background: #161b22; border-color: #30363d; }
    .ron-suffix-box { background: #1f6feb; color: #fff; border: 1px solid #1f6feb; }
    .money-input-wrap .stTextInput>div>div>input { border-radius: 6px 0 0 6px !important; border-right: none !important; }
    .ratio-val { color: #79c0ff; }
    .section-lbl { color: #8b949e; }
    hr { border-color: #21262d !important; }
    .stCheckbox label span { color: #c9d1d9 !important; }
    </style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>
    .stApp { background: #f6f8fa; }
    section[data-testid="stSidebar"] { background: #fff; border-right: 1px solid #d0d7de; }
    div[data-testid="stExpander"] { background: #fff; border: 1px solid #d0d7de; }
    div[data-testid="stForm"] { background: #fff; border: 1px solid #d0d7de; }
    .ron-suffix-box { background: #1a73e8; color: #fff; border: 1px solid #1a73e8; }
    .money-input-wrap .stTextInput>div>div>input { border-radius: 6px 0 0 6px !important; border-right: none !important; }
    .ratio-val { color: #1a73e8; }
    .section-lbl { color: #57606a; }
    </style>""", unsafe_allow_html=True)

st.markdown("""<style>
.block-container { padding-top: 1rem; max-width: 1050px; }
h1 { font-size: 1.4rem !important; margin-bottom: 0 !important; }
.ron-suffix-box {
    display: inline-flex; align-items: center; justify-content: center;
    padding: 0 0.65rem; border-radius: 0 6px 6px 0;
    font-weight: 700; font-size: 0.8rem; letter-spacing: 0.04rem;
    height: 42px; margin-top: 1.65rem;
}
.ratio-val { font-size: 1rem; font-weight: 700; margin-top: 1.9rem; }
.section-lbl {
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08rem;
    font-weight: 600; margin: 0.6rem 0 0.15rem 0;
}
div[data-testid="stNumberInput"] { margin-bottom: -0.3rem; }
</style>""", unsafe_allow_html=True)

floor_labels = [floor_name(f, lang) for f in FLOOR_OPTS]


def _money(label, key, placeholder):
    """Unified money input: [amount|RON] as one visual component."""
    st.markdown('<div class="money-input-wrap">', unsafe_allow_html=True)
    c1, c2 = st.columns([7, 1])
    with c1:
        val = st.text_input(label, value="", placeholder=placeholder, key=key)
    with c2:
        st.markdown('<div class="ron-suffix-box">RON</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return val


def _section(label):
    st.markdown(f'<div class="section-lbl">{label}</div>', unsafe_allow_html=True)


# =============================================================================
# MONTHLY INPUT
# =============================================================================
if page == "monthly":
    st.markdown(f"## {t('tab_monthly', lang)}")
    ph = t("input_placeholder", lang)
    eph = t("ext_placeholder", lang)

    c1, c2 = st.columns(2)
    with c1:
        month = st.selectbox(t("month", lang), range(1, 13),
            index=datetime.now().month - 1,
            format_func=lambda m: month_name(m, lang))
    with c2:
        year = st.number_input(t("year", lang), min_value=2020,
            max_value=datetime.now().year + 5, value=datetime.now().year)

    _section(t("invoice_totals", lang))
    i1, i2, i3 = st.columns(3)
    with i1:
        inp_elec = _money(t("electricity", lang), "inp_elec", ph)
        inp_hgas = _money(t("hotel_gas", lang), "inp_hgas", ph)
    with i2:
        inp_water = _money(t("water", lang), "inp_water", ph)
        inp_gfgas = _money(t("ground_floor_gas", lang), "inp_gfgas", ph)
    with i3:
        inp_garbage = _money(t("garbage", lang), "inp_garbage", ph)
        inp_ffgas = _money(t("first_floor_gas", lang), "inp_ffgas", ph)

    _section(t("external_usage", lang))
    e1, e2, e3 = st.columns(3)
    with e1:
        ext_elec = _money(t("external_electricity", lang), "ext_elec", eph)
        ext_hgas = _money(t("external_hotel_gas", lang), "ext_hgas", eph)
    with e2:
        ext_water = _money(t("external_water", lang), "ext_water", eph)
        ext_gfgas = _money(t("external_gf_gas", lang), "ext_gfgas", eph)
    with e3:
        ext_garbage = _money(t("external_garbage", lang), "ext_garbage", eph)
        ext_ffgas = _money(t("external_ff_gas", lang), "ext_ffgas", eph)

    st.markdown("")
    if st.button(t("generate", lang), type="primary", use_container_width=True):
        raw_fields = [
            (t("electricity", lang), inp_elec), (t("water", lang), inp_water),
            (t("garbage", lang), inp_garbage), (t("hotel_gas", lang), inp_hgas),
            (t("ground_floor_gas", lang), inp_gfgas), (t("first_floor_gas", lang), inp_ffgas),
            (t("external_electricity", lang), ext_elec), (t("external_water", lang), ext_water),
            (t("external_garbage", lang), ext_garbage), (t("external_hotel_gas", lang), ext_hgas),
            (t("external_gf_gas", lang), ext_gfgas), (t("external_ff_gas", lang), ext_ffgas),
        ]
        parsed, errors = {}, []
        for lbl, raw in raw_fields:
            try:
                parsed[lbl] = parse_ron_input(raw)
            except (ValueError, AttributeError):
                errors.append(lbl)

        if errors:
            st.error(t("invalid_number", lang, fields=", ".join(errors)))
        else:
            vals = list(parsed.values())
            mi = {
                "electricity_total": vals[0], "water_total": vals[1], "garbage_total": vals[2],
                "hotel_gas_total": vals[3], "ground_floor_gas_total": vals[4], "first_floor_gas_total": vals[5],
                "external_electricity": vals[6], "external_water": vals[7], "external_garbage": vals[8],
                "external_hotel_gas": vals[9], "external_gf_gas": vals[10], "external_ff_gas": vals[11],
            }
            active = [c for c in st.session_state.companies if c["active"]]
            if not active:
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
                err = False
                for tk, ek, fl in checks:
                    if mi[ek] > mi[tk]:
                        st.error(t("external_exceeds", lang, field=fl, ext=mi[ek], total=mi[tk]))
                        err = True
                if not err:
                    settings = st.session_state.settings
                    results = allocate_costs(st.session_state.companies, settings["ratios"], mi)
                    if not results:
                        st.warning(t("no_results", lang))
                    else:
                        _section(t("preview", lang))
                        cols_def = [
                            (t("excel_company", lang), "company_name", False),
                            (t("electricity", lang)[:5], "electricity", True),
                            (t("water", lang)[:5], "water", True),
                            (t("garbage", lang)[:5], "garbage", True),
                            ("Gas(H)", "gas_hotel", True),
                            ("Gas(GF)", "gas_ground_floor", True),
                            ("Gas(1F)", "gas_first_floor", True),
                            (t("excel_total", lang), "total", True),
                        ]
                        hc = st.columns([3] + [1] * 7)
                        for i, (lbl, _, _) in enumerate(cols_def):
                            hc[i].markdown(f"**{lbl}**")
                        for r in results:
                            rc = st.columns([3] + [1] * 7)
                            for i, (_, key, is_num) in enumerate(cols_def):
                                v = r[key]
                                rc[i].write(format_ron(v) if is_num else v)

                        mn = month_name(month, lang)
                        fn = f"Premier_BC_{year}_{month:02d}_{mn}.xlsx"
                        tp = os.path.join(tempfile.gettempdir(), fn)
                        generate_excel(tp, results, mi, settings["ratios"], active, lang)
                        save_run(month, year, lang, mi, settings["ratios"],
                                 st.session_state.companies, results, tp)
                        with open(tp, "rb") as f:
                            st.download_button(f"{t('download', lang)} {fn}", data=f,
                                file_name=fn,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary", use_container_width=True)

# =============================================================================
# COMPANIES
# =============================================================================
elif page == "companies":
    st.markdown(f"## {t('tab_companies', lang)}")
    companies = st.session_state.companies

    # --- Add New (collapsed) ---
    with st.expander(f"+ {t('add_company', lang)}", expanded=False):
        with st.form("add_company_form"):
            _section(t("basic_info", lang))
            a1, a2, a3, a4 = st.columns(4)
            with a1:
                add_name = st.text_input(t("company_name", lang))
            with a2:
                add_area = st.number_input(t("area_m2", lang), min_value=0.0, step=0.01)
            with a3:
                add_hc = st.number_input(t("persons", lang), min_value=0, step=1, value=1)
            with a4:
                add_fi = st.selectbox(t("floor", lang), range(len(FLOOR_OPTS)),
                    format_func=lambda i: floor_labels[i])
                add_floor = FLOOR_OPTS[add_fi]

            ab1, ab2 = st.columns([1, 3])
            with ab1:
                add_building = st.text_input(t("building", lang), value="C4")

            _section(t("utility_eligibility", lang))
            au1, au2, au3, au4 = st.columns(4)
            with au1:
                add_heat = st.checkbox(t("has_heating", lang), value=True)
            with au2:
                add_elec = st.checkbox(t("electricity", lang), value=True)
            with au3:
                add_water = st.checkbox(t("water", lang), value=True)
            with au4:
                add_garb = st.checkbox(t("garbage", lang), value=True)

            _section(t("contact_details", lang))
            ao1, ao2, ao3, ao4 = st.columns(4)
            with ao1:
                add_contact = st.text_input(t("contact_person", lang), key="add_contact")
                add_phone = st.text_input(t("phone", lang), key="add_phone")
            with ao2:
                add_email = st.text_input(t("email", lang), key="add_email")
                add_office = st.text_input(t("office_location", lang), key="add_office")
            with ao3:
                add_begin = st.text_input(t("beginning_date", lang), key="add_begin")
                add_expire = st.text_input(t("expiration_date", lang), key="add_expire")
            with ao4:
                add_notes = st.text_area(t("notes", lang), key="add_notes", height=68)

            submitted = st.form_submit_button(t("add_company", lang), type="primary")
            if submitted:
                existing_names = [x["name"].strip().lower() for x in companies]
                existing_ids = [x["id"] for x in companies]
                cid = re.sub(r"[^a-z0-9]+", "-", add_name.strip().lower()).strip("-")
                if not add_name.strip():
                    st.error(t("name_empty", lang))
                elif add_name.strip().lower() in existing_names:
                    st.error(t("name_exists", lang, name=add_name))
                elif cid in existing_ids:
                    st.error(t("id_exists", lang))
                elif add_area <= 0:
                    st.error(t("area_zero", lang))
                else:
                    add_company({
                        "id": cid, "name": add_name.strip(), "area_m2": add_area,
                        "headcount_default": add_hc, "building": add_building, "floor": add_floor,
                        "has_heating": add_heat, "electricity_eligible": add_elec,
                        "water_eligible": add_water, "garbage_eligible": add_garb, "active": True,
                        "office_location": add_office, "contact_person": add_contact,
                        "phone": add_phone, "email": add_email,
                        "beginning_date": add_begin, "expiration_date": add_expire, "notes": add_notes,
                    })
                    st.session_state._reload = True
                    st.success(t("added_ok", lang, name=add_name))
                    st.rerun()

    # --- Company List ---
    for idx, c in enumerate(companies, 1):
        icon = "🟢" if c["active"] else "🔴"
        lbl = f'{t("company_no", lang)} {idx} {icon} {c["name"]} \u2014 {c["area_m2"]} m\u00b2, {c["headcount_default"]} {t("excel_persons", lang).lower()}'
        with st.expander(lbl):
            _section(t("basic_info", lang))
            b1, b2, b3, b4 = st.columns(4)
            with b1:
                nn = st.text_input(t("company_name", lang), value=c["name"], key=f"en_{c['id']}")
            with b2:
                na = st.number_input(t("area_m2", lang), value=c["area_m2"], key=f"ea_{c['id']}", step=0.01)
            with b3:
                nh = st.number_input(t("persons", lang), value=c["headcount_default"], min_value=0, key=f"eh_{c['id']}", step=1)
            with b4:
                nfi = st.selectbox(t("floor", lang), range(len(FLOOR_OPTS)),
                    index=FLOOR_OPTS.index(c["floor"]),
                    format_func=lambda i: floor_labels[i], key=f"ef_{c['id']}")
                nf = FLOOR_OPTS[nfi]
            bb1, bb2 = st.columns([1, 3])
            with bb1:
                nb = st.text_input(t("building", lang), value=c["building"], key=f"eb_{c['id']}")

            _section(t("utility_eligibility", lang))
            u1, u2, u3, u4, u5 = st.columns(5)
            with u1:
                nht = st.checkbox(t("has_heating", lang), value=c["has_heating"], key=f"eht_{c['id']}")
            with u2:
                nel = st.checkbox(t("electricity", lang), value=c["electricity_eligible"], key=f"eel_{c['id']}")
            with u3:
                nwa = st.checkbox(t("water", lang), value=c["water_eligible"], key=f"ewa_{c['id']}")
            with u4:
                nga = st.checkbox(t("garbage", lang), value=c["garbage_eligible"], key=f"ega_{c['id']}")
            with u5:
                nac = st.checkbox(t("active", lang), value=c["active"], key=f"eac_{c['id']}")

            _section(t("contact_details", lang))
            o1, o2, o3, o4 = st.columns(4)
            with o1:
                nco = st.text_input(t("contact_person", lang), value=c.get("contact_person", ""), key=f"eco_{c['id']}")
                nph = st.text_input(t("phone", lang), value=c.get("phone", ""), key=f"eph_{c['id']}")
            with o2:
                nem = st.text_input(t("email", lang), value=c.get("email", ""), key=f"eem_{c['id']}")
                nof = st.text_input(t("office_location", lang), value=c.get("office_location", ""), key=f"eof_{c['id']}")
            with o3:
                nbd = st.text_input(t("beginning_date", lang), value=c.get("beginning_date", ""), key=f"ebd_{c['id']}")
                ned = st.text_input(t("expiration_date", lang), value=c.get("expiration_date", ""), key=f"eed_{c['id']}")
            with o4:
                nno = st.text_area(t("notes", lang), value=c.get("notes", ""), key=f"eno_{c['id']}", height=68)

            if st.button(t("save", lang), key=f"sv_{c['id']}", type="primary"):
                oth = [x["name"].strip().lower() for x in companies if x["id"] != c["id"]]
                if nn.strip().lower() in oth:
                    st.error(t("name_exists", lang, name=nn))
                elif not nn.strip():
                    st.error(t("name_empty", lang))
                elif na <= 0:
                    st.error(t("area_zero", lang))
                elif nh < 0:
                    st.error(t("persons_negative", lang))
                else:
                    update_company(c["id"], {
                        "name": nn.strip(), "area_m2": na, "headcount_default": nh,
                        "floor": nf, "building": nb, "has_heating": nht,
                        "electricity_eligible": nel, "water_eligible": nwa,
                        "garbage_eligible": nga, "active": nac,
                        "office_location": nof, "contact_person": nco,
                        "phone": nph, "email": nem,
                        "beginning_date": nbd, "expiration_date": ned, "notes": nno,
                    })
                    st.session_state._reload = True
                    st.success(t("saved_ok", lang, name=nn))
                    st.rerun()

# =============================================================================
# SETTINGS
# =============================================================================
elif page == "settings":
    st.markdown(f"## {t('tab_settings', lang)}")
    saved = st.session_state.settings

    _section(t("ratios_title", lang))
    st.caption(t("ratios_help", lang))

    pending = {}
    changed = False
    for et in ["electricity", "gas", "water", "garbage"]:
        cur = saved["ratios"][et]
        c1, c2 = st.columns([2, 1])
        with c1:
            ns = st.number_input(t("sqm_pct", lang, type=et.capitalize()),
                min_value=0, max_value=100, value=cur["sqm_weight"],
                step=5, key=f"rs_{et}")
        with c2:
            pp = 100 - ns
            st.markdown(f'<div class="ratio-val">{t("person_pct", lang, type=et.capitalize())}: {pp}%</div>',
                        unsafe_allow_html=True)
        pending[et] = {"sqm_weight": ns, "headcount_weight": pp}
        if ns != cur["sqm_weight"]:
            changed = True

    if changed:
        st.warning(t("unsaved_warning", lang))
        if st.button(t("save_settings", lang), type="primary"):
            saved["ratios"] = pending
            save_settings(saved)
            st.session_state._reload = True
            st.success(t("settings_saved", lang))
            st.rerun()

    st.divider()

    _section(t("language", lang))
    lang_opts = {"English": "en", "Romana": "ro"}
    lang_names = list(lang_opts.keys())
    cur_idx = lang_names.index("Romana" if lang == "ro" else "English")
    new_lang_label = st.selectbox(t("language", lang), lang_names, index=cur_idx,
                                  key="settings_lang", label_visibility="collapsed")
    new_lang = lang_opts[new_lang_label]
    if new_lang != lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.divider()

    _section(t("appearance", lang))
    theme_opts = [t("theme_light", lang), t("theme_dark", lang)]
    cur_theme_idx = 1 if is_dark else 0
    new_theme = st.radio(t("appearance", lang), theme_opts, index=cur_theme_idx,
                         horizontal=True, label_visibility="collapsed")
    want_dark = new_theme == t("theme_dark", lang)
    if want_dark != is_dark:
        st.session_state.theme = "dark" if want_dark else "light"
        st.rerun()

# =============================================================================
# HISTORY
# =============================================================================
elif page == "history":
    st.markdown(f"## {t('history_title', lang)}")
    runs = list_runs()
    if not runs:
        st.info(t("history_empty", lang))
    else:
        for entry in runs:
            mn = month_name(entry["month"], entry.get("language", "en"))
            rl = t("history_run", lang, month=mn, year=entry["year"])
            gd = entry["generated_at"][:10]
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(f"**{rl}** &nbsp; {t('history_generated', lang, date=gd)}")
            with c2:
                ep = get_excel_path(entry)
                if os.path.exists(ep):
                    with open(ep, "rb") as f:
                        st.download_button(t("history_download", lang), data=f,
                            file_name=os.path.basename(ep),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{entry['id']}")
            with c3:
                if st.button(t("history_delete", lang), key=f"del_{entry['id']}"):
                    delete_run(entry["id"])
                    st.success(t("history_deleted", lang))
                    st.rerun()
