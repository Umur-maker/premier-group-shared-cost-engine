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


def generate_statement_pdf(filepath, company, result, month, year, monthly_input, lang="en"):
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
    stmt_title = "Monthly Shared Expense Statement" if lang == "en" else "Extras Lunar Costuri Comune"
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
    info_label = "Company Information" if lang == "en" else "Informatii Companie"
    elements.append(Paragraph(info_label, s_section))

    info_rows = []
    label_map = [
        ("excel_company", "name"),
        ("office_location", "office_location"),
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
    breakdown_label = "Expense Breakdown" if lang == "en" else "Detaliere Cheltuieli"
    elements.append(Paragraph(breakdown_label, s_section))

    header_row = [
        "Expense Category" if lang == "en" else "Categorie Cheltuiala",
        "Amount (RON)" if lang == "en" else "Suma (RON)",
    ]
    expense_rows = []
    expenses = [
        (t("electricity", lang), result["electricity"]),
        (t("water", lang), result["water"]),
        (t("garbage", lang), result["garbage"]),
        (t("excel_gas_hotel", lang), result["gas_hotel"]),
        (t("excel_gas_gf", lang), result["gas_ground_floor"]),
        (t("excel_gas_ff", lang), result["gas_first_floor"]),
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
    if lang == "en":
        note = (
            "This statement reflects your share of the shared building costs "
            "for the above period. Amounts are calculated based on your allocated "
            "area (m\u00b2) and number of persons, according to the cost sharing "
            "agreement of Premier Business Center."
        )
    else:
        note = (
            "Acest extras reflecta cota dumneavoastra din costurile comune ale "
            "cladirii pentru perioada de mai sus. Sumele sunt calculate pe baza "
            "suprafetei alocate (m\u00b2) si a numarului de persoane, conform "
            "acordului de partajare a costurilor al Premier Business Center."
        )
    elements.append(Paragraph(note, s_note))

    doc.build(elements)
    return filepath
