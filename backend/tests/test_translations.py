from backend.core.translations import t, floor_name, month_name, TRANSLATIONS, MONTH_NAMES


def test_english_title():
    assert "Premier Business Center" in t("app_title", "en")


def test_romanian_title():
    assert "Premier Business Center" in t("app_title", "ro")


def test_no_headcount_in_translations():
    for lang in ("en", "ro"):
        for key, val in TRANSLATIONS[lang].items():
            assert "headcount" not in val.lower() or "headcount_weight" in val.lower() or "hc" in key, \
                f"Found 'headcount' in {lang}.{key}: {val}"


def test_floor_names():
    assert floor_name("ground_floor", "en") == "Ground Floor"
    assert floor_name("ground_floor", "ro") == "Parter"
    assert floor_name("hotel", "en") == "Hotel"


def test_format_substitution():
    result = t("external_exceeds", "en", field="Water", ext=150.0, total=100.0)
    assert "150.00" in result
    assert "100.00" in result
    assert "RON" in result


def test_unknown_key_returns_key():
    assert t("nonexistent_key_xyz", "en") == "nonexistent_key_xyz"


def test_auto_balance_label():
    sqm_label = t("sqm_pct", "en", type="Electricity")
    assert "sqm" in sqm_label.lower()
    person_label = t("person_pct", "en", type="Electricity")
    assert "person" in person_label.lower()


# --- Month name translations ---

def test_month_names_english():
    assert month_name(1, "en") == "January"
    assert month_name(12, "en") == "December"


def test_month_names_romanian():
    assert month_name(1, "ro") == "Ianuarie"
    assert month_name(2, "ro") == "Februarie"
    assert month_name(12, "ro") == "Decembrie"


def test_month_names_all_12():
    for lang in ("en", "ro"):
        assert len(MONTH_NAMES[lang]) == 12


def test_ron_in_labels():
    """Key money labels should mention RON."""
    assert "RON" in t("invoice_totals", "en")
    assert "RON" in t("external_usage", "en")
    assert "RON" in t("preview", "en")
    assert "RON" in t("excel_total_payment", "en")
    assert "RON" in t("invoice_totals", "ro")
