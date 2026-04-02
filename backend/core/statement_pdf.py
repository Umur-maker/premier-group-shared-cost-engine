"""Generate a company-specific cost sharing statement as PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from backend.core.translations import t, month_name


BLUE = HexColor("#4472C4")
LIGHT_GRAY = HexColor("#f5f5f5")
RON_FMT = lambda v: f"{v:,.2f} RON".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_statement_pdf(filepath, company, result, month, year, monthly_input, lang="en"):
    """Generate a single-company cost sharing statement as PDF."""
    doc = SimpleDocTemplate(filepath, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm, topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18,
        textColor=BLUE, spaceAfter=2*mm)
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=13,
        textColor=HexColor("#333333"), spaceBefore=1*mm, spaceAfter=1*mm)
    period_style = ParagraphStyle("Period", parent=styles["Normal"], fontSize=11,
        textColor=HexColor("#666666"), spaceAfter=6*mm)
    note_style = ParagraphStyle("Note", parent=styles["Normal"], fontSize=8,
        textColor=HexColor("#888888"), spaceBefore=8*mm, leading=11)

    elements = []

    # Header
    elements.append(Paragraph("Premier Business Center", title_style))

    stmt_title = "Monthly Shared Expense Statement" if lang == "en" else "Extras Lunar Costuri Comune"
    elements.append(Paragraph(stmt_title, subtitle_style))

    mn = month_name(month, lang)
    elements.append(Paragraph(f"{mn} {year}", period_style))

    # Company info table
    info_data = [[t("excel_company", lang), company["name"]]]
    if company.get("office_location"):
        info_data.append([t("office_location", lang), company["office_location"]])
    if company.get("contact_person"):
        info_data.append([t("contact_person", lang), company["contact_person"]])

    info_table = Table(info_data, colWidths=[45*mm, 110*mm])
    info_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#666666")),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
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
    expense_table = Table(table_data, colWidths=[100*mm, 55*mm])

    table_style = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        # Body
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        # Total row
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_GRAY),
    ]
    # Alternate row colors
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
