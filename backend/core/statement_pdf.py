"""Generate a company-specific cost sharing statement as PDF."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.core.translations import t, month_name

NAVY = HexColor("#1a2d5a")
RED = HexColor("#e31e24")
LIGHT_GRAY = HexColor("#f5f6f8")
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
RON_FMT = lambda v: f"{v:,.2f} RON".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_statement_pdf(filepath, company, result, month, year, monthly_input, lang="en"):
    """Generate a single-company cost sharing statement as PDF."""
    doc = SimpleDocTemplate(filepath, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm, topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=16,
        textColor=NAVY, spaceAfter=1*mm)
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=12,
        textColor=RED, spaceBefore=1*mm, spaceAfter=1*mm, fontName="Helvetica-Bold")
    period_style = ParagraphStyle("Period", parent=styles["Normal"], fontSize=11,
        textColor=HexColor("#666666"), spaceAfter=6*mm)
    note_style = ParagraphStyle("Note", parent=styles["Normal"], fontSize=8,
        textColor=HexColor("#888888"), spaceBefore=8*mm, leading=11)

    elements = []

    # Logo — preserve original aspect ratio
    if os.path.exists(LOGO_PATH):
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(LOGO_PATH)
        iw, ih = img_reader.getSize()
        logo_width = 60*mm
        logo_height = logo_width * (ih / iw)
        logo = Image(LOGO_PATH, width=logo_width, height=logo_height)
        elements.append(logo)
        elements.append(Spacer(1, 3*mm))

    # Title
    stmt_title = "Monthly Shared Expense Statement" if lang == "en" else "Extras Lunar Costuri Comune"
    elements.append(Paragraph(stmt_title, subtitle_style))

    mn = month_name(month, lang)
    elements.append(Paragraph(f"{mn} {year}", period_style))

    # Divider line
    div_table = Table([[""]], colWidths=[160*mm])
    div_table.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 1, NAVY)]))
    elements.append(div_table)
    elements.append(Spacer(1, 4*mm))

    # Company info
    info_data = [[t("excel_company", lang), company["name"]]]
    if company.get("office_location"):
        info_data.append([t("office_location", lang), company["office_location"]])
    if company.get("contact_person"):
        info_data.append([t("contact_person", lang), company["contact_person"]])

    info_table = Table(info_data, colWidths=[45*mm, 115*mm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#666666")),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (1, 0), (1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    # Expense breakdown
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

    total_label = t("excel_total", lang)
    total_row = [total_label, RON_FMT(result["total"])]

    table_data = [header_row] + expense_rows + [total_row]
    expense_table = Table(table_data, colWidths=[100*mm, 60*mm])

    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#d0d0d0")),
        # Total row
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("BACKGROUND", (0, -1), (-1, -1), NAVY),
        ("TEXTCOLOR", (0, -1), (-1, -1), HexColor("#FFFFFF")),
        ("TOPPADDING", (0, -1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
    ]
    for i in range(1, len(expense_rows) + 1):
        if i % 2 == 0:
            table_style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))

    expense_table.setStyle(TableStyle(table_style))
    elements.append(expense_table)

    # Note
    if lang == "en":
        note = (
            "This statement reflects your share of the shared building costs "
            "for the above period. Amounts are calculated based on your allocated "
            "area (m²) and number of persons, according to the cost sharing agreement "
            "of Premier Business Center."
        )
    else:
        note = (
            "Acest extras reflecta cota dumneavoastra din costurile comune ale cladirii "
            "pentru perioada de mai sus. Sumele sunt calculate pe baza suprafetei alocate "
            "(m²) si a numarului de persoane, conform acordului de partajare a costurilor "
            "al Premier Business Center."
        )
    elements.append(Paragraph(note, note_style))

    doc.build(elements)
    return filepath
