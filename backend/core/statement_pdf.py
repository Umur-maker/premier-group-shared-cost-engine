"""Generate a company-specific cost sharing statement as PDF."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
)
from reportlab.lib.styles import ParagraphStyle
from backend.core.translations import t, month_name

NAVY = HexColor("#1a2d5a")
GRAY_600 = HexColor("#6b7280")
GRAY_400 = HexColor("#9ca3af")
GRAY_200 = HexColor("#e5e7eb")
GRAY_50 = HexColor("#f9fafb")
WHITE = HexColor("#ffffff")
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
RON_FMT = lambda v: f"{v:,.2f} RON".replace(",", "X").replace(".", ",").replace("X", ".")

PAGE_W = A4[0]
CONTENT_W = PAGE_W - 50 * mm  # 25mm margins each side


def generate_statement_pdf(filepath, company, result, month, year, monthly_input, lang="en", eur_rate=None):
    doc = SimpleDocTemplate(filepath, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm, topMargin=20*mm, bottomMargin=20*mm)

    # Styles
    s_title = ParagraphStyle("s_title", fontName="Helvetica-Bold", fontSize=13,
        textColor=NAVY, leading=16)
    s_subtitle = ParagraphStyle("s_subtitle", fontName="Helvetica", fontSize=10,
        textColor=GRAY_600, leading=13)
    s_period = ParagraphStyle("s_period", fontName="Helvetica", fontSize=10,
        textColor=GRAY_400, leading=13)
    s_section = ParagraphStyle("s_section", fontName="Helvetica-Bold", fontSize=9,
        textColor=NAVY, spaceBefore=0, spaceAfter=3*mm, leading=12)
    s_note = ParagraphStyle("s_note", fontName="Helvetica", fontSize=7.5,
        textColor=GRAY_400, spaceBefore=10*mm, leading=10)

    elements = []

    # ── HEADER: logo left, text right ──
    _stmt_titles = {"en": "Monthly Shared Expense Statement", "ro": "Extras Lunar Costuri Comune", "tr": "Aylık Ortak Gider Ekstresi"}
    stmt_title = _stmt_titles.get(lang, _stmt_titles["en"])
    mn = month_name(month, lang)

    header_right = [
        [Paragraph("Premier Business Center", s_title)],
        [Paragraph(stmt_title, s_subtitle)],
        [Paragraph(f"{mn} {year}", s_period)],
    ]
    right_table = Table(header_right, colWidths=[95*mm])
    right_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))

    if os.path.exists(LOGO_PATH):
        img_reader = ImageReader(LOGO_PATH)
        iw, ih = img_reader.getSize()
        logo_w = 50 * mm
        logo_h = logo_w * (ih / iw)
        logo = Image(LOGO_PATH, width=logo_w, height=logo_h)

        header_table = Table(
            [[logo, right_table]],
            colWidths=[55*mm, CONTENT_W - 55*mm],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(header_table)
    else:
        elements.append(right_table)

    elements.append(Spacer(1, 4*mm))

    # ── SEPARATOR ──
    sep = Table([[""]], colWidths=[CONTENT_W])
    sep.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.5, GRAY_200)]))
    elements.append(sep)
    elements.append(Spacer(1, 6*mm))

    # ── COMPANY INFO ──
    _info_labels = {"en": "Company Information", "ro": "Informatii Companie", "tr": "Firma Bilgileri"}
    info_label = _info_labels.get(lang, _info_labels["en"])
    elements.append(Paragraph(info_label, s_section))

    info_rows = []
    label_map = [
        ("excel_company", "name"),
        ("office_location", "office_no"),
        ("contact_person", "contact_person"),
    ]
    for tkey, ckey in label_map:
        val = company.get(ckey, "")
        if val:
            info_rows.append([t(tkey, lang), val])

    if info_rows:
        info_table = Table(info_rows, colWidths=[40*mm, CONTENT_W - 40*mm])
        info_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (0, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), GRAY_400),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
            ("FONTSIZE", (1, 0), (1, -1), 10),
            ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
            ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (1, 0), (1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(info_table)

    elements.append(Spacer(1, 8*mm))

    # ── EXPENSE BREAKDOWN ──
    _breakdown_labels = {"en": "Expense Breakdown", "ro": "Detaliere Cheltuieli", "tr": "Gider Dağılımı"}
    breakdown_label = _breakdown_labels.get(lang, _breakdown_labels["en"])
    elements.append(Paragraph(breakdown_label, s_section))

    _cat_headers = {"en": "Expense Category", "ro": "Categorie Cheltuiala", "tr": "Gider Kategorisi"}
    _amt_headers = {"en": "Amount (RON)", "ro": "Suma (RON)", "tr": "Tutar (RON)"}
    header_row = [
        _cat_headers.get(lang, _cat_headers["en"]),
        _amt_headers.get(lang, _amt_headers["en"]),
    ]
    expense_rows = []
    expenses = [
        (t("electricity", lang), result["electricity"]),
        (t("water", lang), result["water"]),
        (t("garbage", lang), result["garbage"]),
        (t("excel_gas_hotel", lang), result["gas_hotel"]),
        (t("excel_gas_gf", lang), result["gas_ground_floor"]),
        (t("excel_gas_ff", lang), result["gas_first_floor"]),
        (t("consumables", lang), result.get("consumables", 0)),
        (t("printer", lang), result.get("printer", 0)),
        (t("internet", lang), result.get("internet", 0)),
        (t("maintenance", lang) + (f" ({company.get('maintenance_rate_eur', 0):.2f} EUR \u00d7 {eur_rate})" if eur_rate and company.get("maintenance_rate_eur", 0) > 0 else ""), result.get("maintenance", 0)),
        (t("maintenance_vat", lang), result.get("maintenance_vat", 0)),
        (t("rent", lang) + (f" ({company.get('monthly_rent_eur', 0):.2f} EUR \u00d7 {eur_rate})" if eur_rate and company.get("monthly_rent_eur", 0) > 0 else ""), result.get("rent", 0)),
        (t("rent_vat", lang), result.get("rent_vat", 0)),
    ]
    for label, amount in expenses:
        if amount > 0:
            expense_rows.append([label, RON_FMT(amount)])

    table_data = [header_row] + expense_rows
    expense_table = Table(table_data, colWidths=[CONTENT_W - 55*mm, 55*mm])

    style = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TEXTCOLOR", (0, 1), (-1, -1), HexColor("#374151")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, GRAY_200),
    ]
    # Zebra
    for i in range(1, len(expense_rows) + 1):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), GRAY_50))

    expense_table.setStyle(TableStyle(style))
    elements.append(expense_table)
    elements.append(Spacer(1, 2*mm))

    # ── TOTAL ──
    total_label = t("excel_total", lang)
    total_table = Table(
        [[total_label, RON_FMT(result["total"])]],
        colWidths=[CONTENT_W - 55*mm, 55*mm],
    )
    total_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 13),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
    ]))
    elements.append(total_table)

    # ── FOOTER NOTE ──
    _notes = {
        "en": (
            "This statement reflects your share of the shared building costs "
            "for the above period. Amounts are calculated based on your allocated "
            "area (m\u00b2) and number of persons, according to the cost sharing "
            "agreement of Premier Business Center."
        ),
        "ro": (
            "Acest extras reflecta cota dumneavoastra din costurile comune ale "
            "cladirii pentru perioada de mai sus. Sumele sunt calculate pe baza "
            "suprafetei alocate (m\u00b2) si a numarului de persoane, conform "
            "acordului de partajare a costurilor al Premier Business Center."
        ),
        "tr": (
            "Bu ekstre, yukar\u0131daki d\u00f6nem i\u00e7in ortak bina giderlerinden "
            "size d\u00fc\u015fen pay\u0131 yans\u0131tmaktad\u0131r. Tutarlar, Premier Business Center "
            "maliyet payla\u015f\u0131m s\u00f6zle\u015fmesine g\u00f6re tahsis edilen alan\u0131n\u0131za (m\u00b2) "
            "ve ki\u015fi say\u0131n\u0131za g\u00f6re hesaplanm\u0131\u015ft\u0131r."
        ),
    }
    note = _notes.get(lang, _notes["en"])
    elements.append(Paragraph(note, s_note))

    doc.build(elements)
    return filepath
