"""Generate a per-company Cost Sharing Agreement PDF for signature."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak,
)
from reportlab.lib.styles import ParagraphStyle

NAVY = HexColor("#1a2d5a")
RED = HexColor("#e31e24")
GRAY = HexColor("#6b7280")
GRAY_LIGHT = HexColor("#9ca3af")
GRAY_BG = HexColor("#f9fafb")
GRAY_BORDER = HexColor("#d1d5db")
WHITE = HexColor("#ffffff")
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")

PAGE_W = A4[0]
CONTENT_W = PAGE_W - 50 * mm


def generate_agreement_pdf(filepath, company, settings, lang="en", all_companies=None):
    """Generate a cost sharing agreement PDF for a specific company."""
    # Collect eligible company names dynamically (if provided)
    def _names_for(flag):
        if not all_companies:
            return "eligible companies"
        names = [c["name"] for c in all_companies if c.get("active") and c.get(flag)]
        return ", ".join(names) if names else "-"

    printer_names = _names_for("printer_eligible")
    internet_names = _names_for("internet_eligible")
    consumables_names = _names_for("consumables_eligible")
    doc = SimpleDocTemplate(filepath, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm, topMargin=20*mm, bottomMargin=25*mm)

    # Styles
    s_title = ParagraphStyle("s_title", fontName="Helvetica-Bold", fontSize=16,
        textColor=NAVY, alignment=TA_CENTER, leading=20, spaceAfter=2*mm)
    s_subtitle = ParagraphStyle("s_subtitle", fontName="Helvetica-Bold", fontSize=12,
        textColor=RED, alignment=TA_CENTER, leading=15, spaceAfter=6*mm)
    s_h2 = ParagraphStyle("s_h2", fontName="Helvetica-Bold", fontSize=11,
        textColor=NAVY, spaceBefore=6*mm, spaceAfter=3*mm, leading=14)
    s_body = ParagraphStyle("s_body", fontName="Helvetica", fontSize=9.5,
        textColor=HexColor("#374151"), leading=14, spaceAfter=2*mm, alignment=TA_JUSTIFY)
    s_body_bold = ParagraphStyle("s_body_bold", fontName="Helvetica-Bold", fontSize=9.5,
        textColor=HexColor("#374151"), leading=14, spaceAfter=2*mm)
    s_small = ParagraphStyle("s_small", fontName="Helvetica", fontSize=8,
        textColor=GRAY, leading=11, spaceAfter=1*mm)
    s_center = ParagraphStyle("s_center", fontName="Helvetica", fontSize=9.5,
        textColor=HexColor("#374151"), alignment=TA_CENTER, leading=14)
    s_sig_label = ParagraphStyle("s_sig_label", fontName="Helvetica", fontSize=9,
        textColor=GRAY, leading=12, spaceBefore=3*mm)

    is_en = lang == "en"
    is_tr = lang == "tr"

    elements = []

    # ── PAGE 1: HEADER + INTRODUCTION ──

    # Logo
    if os.path.exists(LOGO_PATH):
        img_reader = ImageReader(LOGO_PATH)
        iw, ih = img_reader.getSize()
        logo_w = 55 * mm
        logo_h = logo_w * (ih / iw)
        logo = Image(LOGO_PATH, width=logo_w, height=logo_h)
        logo.hAlign = "CENTER"
        elements.append(logo)
        elements.append(Spacer(1, 4*mm))

    # Title
    if is_en:
        elements.append(Paragraph("Cost Sharing Agreement", s_title))
        elements.append(Paragraph("Shared Building Cost Allocation", s_subtitle))
    elif is_tr:
        elements.append(Paragraph("Maliyet Paylasim Sozlesmesi", s_title))
        elements.append(Paragraph("Ortak Bina Gider Dagitimi", s_subtitle))
    else:
        elements.append(Paragraph("Acord de Partajare a Costurilor", s_title))
        elements.append(Paragraph("Alocarea Costurilor Comune ale Cladirii", s_subtitle))

    # Parties
    if is_en:
        elements.append(Paragraph("1. Parties", s_h2))
        elements.append(Paragraph(
            "This agreement is between <b>Premier Capital & Investments Group S.R.L.</b> "
            "(hereinafter \"the Manager\"), responsible for the administration and allocation "
            "of shared building costs at Premier Business Center, and:", s_body))
    elif is_tr:
        elements.append(Paragraph("1. Taraflar", s_h2))
        elements.append(Paragraph(
            "Bu sozlesme, Premier Business Center'daki ortak bina giderlerinin yonetimi ve "
            "dagitimından sorumlu <b>Premier Capital & Investments Group S.R.L.</b> "
            "(bundan sonra \"Yonetici\") ile asagidaki firma arasindadir:", s_body))
    else:
        elements.append(Paragraph("1. Partile", s_h2))
        elements.append(Paragraph(
            "Acest acord este incheiat intre <b>Premier Capital & Investments Group S.R.L.</b> "
            "(denumit in continuare \"Administratorul\"), responsabil cu administrarea si alocarea "
            "costurilor comune ale cladirii la Premier Business Center, si:", s_body))

    # Company info table
    lbl = ["Company / Firma", "Building / Bina", "Floor / Kat",
           "Office / Ofis", "Area / Alan", "Persons / Kisi",
           "Rent / Kira (EUR)", "Maintenance / Bakim (EUR)"]
    floor_labels = {"ground_floor": "Ground Floor / Zemin Kat", "first_floor": "First Floor / 1. Kat",
                    "hotel": "Hotel / Otel"}
    info_data = [
        [lbl[0], company["name"]],
        [lbl[1], company.get("building", "")],
        [lbl[2], floor_labels.get(company.get("floor", ""), company.get("floor", ""))],
        [lbl[3], company.get("office_no", "")],
        [lbl[4], f"{company.get('area_m2', 0)} m\u00b2"],
        [lbl[5], str(company.get("headcount_default", 0))],
    ]
    rent_eur = company.get("monthly_rent_eur", 0)
    maint_eur = company.get("maintenance_rate_eur", 0)
    if rent_eur > 0:
        info_data.append([lbl[6], f"{rent_eur:,.2f} EUR"])
    if maint_eur > 0:
        info_data.append([lbl[7], f"{maint_eur:,.2f} EUR"])
    info_table = Table(info_data, colWidths=[45*mm, CONTENT_W - 45*mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GRAY),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (1, 0), (1, 0), 11),
        ("GRID", (0, 0), (-1, -1), 0.3, GRAY_BORDER),
        ("BACKGROUND", (0, 0), (0, -1), GRAY_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4*mm))

    # ── METHODOLOGY ──
    if is_en:
        elements.append(Paragraph("2. Allocation Methodology", s_h2))
        elements.append(Paragraph(
            "Shared building costs are distributed among all tenant companies based on a weighted "
            "formula that considers both the office area (m\u00b2) occupied by each company and the "
            "number of persons working in that office. The formula is:", s_body))
        elements.append(Paragraph(
            "<b>Company Share = Net Amount \u00d7 (sqm% \u00d7 Area Ratio + person% \u00d7 Person Ratio)</b>", s_body_bold))
        elements.append(Paragraph(
            "Where Area Ratio = Company m\u00b2 / Total Eligible m\u00b2, and "
            "Person Ratio = Company Persons / Total Eligible Persons.", s_small))
    elif is_tr:
        elements.append(Paragraph("2. Dagitim Yontemi", s_h2))
        elements.append(Paragraph(
            "Ortak bina giderleri, her firmanin isgal ettigi ofis alani (m\u00b2) ve o ofiste calisan "
            "kisi sayisini dikkate alan agirlikli bir formule gore tum kiraci firmalar arasinda "
            "dagitilir. Formul:", s_body))
        elements.append(Paragraph(
            "<b>Firma Payi = Net Tutar \u00d7 (m\u00b2% \u00d7 Alan Orani + kisi% \u00d7 Kisi Orani)</b>", s_body_bold))
        elements.append(Paragraph(
            "Alan Orani = Firma m\u00b2 / Toplam Uygun m\u00b2, "
            "Kisi Orani = Firma Kisileri / Toplam Uygun Kisiler.", s_small))
    else:
        elements.append(Paragraph("2. Metodologia de Alocare", s_h2))
        elements.append(Paragraph(
            "Costurile comune ale cladirii sunt distribuite intre toate companiile chiriase pe baza unei "
            "formule ponderate care ia in considerare atat suprafata biroului (m\u00b2) ocupata de fiecare "
            "companie, cat si numarul de persoane care lucreaza in acel birou. Formula este:", s_body))
        elements.append(Paragraph(
            "<b>Cota Companie = Suma Neta \u00d7 (mp% \u00d7 Raport Suprafata + pers% \u00d7 Raport Persoane)</b>", s_body_bold))
        elements.append(Paragraph(
            "Raport Suprafata = m\u00b2 Companie / Total m\u00b2 Eligibil, "
            "Raport Persoane = Persoane Companie / Total Persoane Eligibile.", s_small))

    # Ratios table
    ratios = settings.get("ratios", {})
    ratio_header = ["Cost Type", "sqm %", "person %"] if is_en else (
        ["Gider Tipi", "m\u00b2 %", "kisi %"] if is_tr else ["Tip Cost", "mp %", "pers %"])
    ratio_data = [ratio_header]
    for key in ["electricity", "gas", "water", "garbage", "consumables"]:
        r = ratios.get(key, {})
        ratio_data.append([key.capitalize(), f"{r.get('sqm_weight', 50)}%", f"{r.get('headcount_weight', 50)}%"])

    ratio_table = Table(ratio_data, colWidths=[50*mm, 30*mm, 30*mm])
    ratio_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, GRAY_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_BG]),
    ]))
    elements.append(ratio_table)
    elements.append(Spacer(1, 3*mm))

    # ── COST CATEGORIES ──
    eur_rate = settings.get("eur_ron_rate", 5.1)

    # Hotel sublet info
    sublet = settings.get("hotel_sublet", {})
    sublet_active = sublet.get("active", False)
    sublet_name = sublet.get("name", "")
    sublet_pct = sublet.get("percentage", 0)

    if is_en:
        elements.append(Paragraph("3. Cost Categories", s_h2))
        categories_text = [
            "Electricity, Water, Garbage - shared among all eligible companies by weighted formula",
            "Gas - split per floor (ground floor / first floor / hotel) by weighted formula",
            f"Consumables (tea, coffee, water) - shared among: {consumables_names}",
            f"Printer - equally shared among: {printer_names}",
            f"Internet - equally shared among: {internet_names}",
            f"Maintenance - fixed EUR amount per company, converted at EUR/RON rate ({eur_rate})",
            f"Rent - fixed EUR amount per company, converted at EUR/RON rate ({eur_rate})",
            "21% VAT is applied on top of Maintenance and Rent amounts",
            "External usage amounts are deducted from invoice totals before allocation",
        ]
        if sublet_active:
            categories_text.append(f"Hotel Sublet: {sublet_pct}% of hotel's utility costs are allocated to {sublet_name} per sublet agreement")
    elif is_tr:
        elements.append(Paragraph("3. Gider Kategorileri", s_h2))
        categories_text = [
            "Elektrik, Su, \u00c7\u00f6p - t\u00fcm uygun firmalar aras\u0131nda a\u011f\u0131rl\u0131kl\u0131 form\u00fclle payla\u015f\u0131l\u0131r",
            "Do\u011falgaz - kat baz\u0131nda b\u00f6l\u00fcn\u00fcr (zemin kat / 1. kat / otel)",
            f"Sarf Malzeme (\u00e7ay, kahve, su) - payla\u015f\u0131l\u0131r: {consumables_names}",
            f"Yaz\u0131c\u0131 - e\u015fit payla\u015f\u0131l\u0131r: {printer_names}",
            f"\u0130nternet - e\u015fit payla\u015f\u0131l\u0131r: {internet_names}",
            f"Bak\u0131m - firma ba\u015f\u0131na sabit EUR tutar\u0131, EUR/RON kuru ({eur_rate}) ile \u00e7evrilir",
            f"Kira - firma ba\u015f\u0131na sabit EUR tutar\u0131, EUR/RON kuru ({eur_rate}) ile \u00e7evrilir",
            "Bak\u0131m ve Kira tutarlar\u0131 \u00fczerine %21 KDV uygulan\u0131r",
            "Harici kullan\u0131m tutarlar\u0131 da\u011f\u0131t\u0131m \u00f6ncesi fatura toplamlar\u0131ndan d\u00fc\u015f\u00fcl\u00fcr",
        ]
        if sublet_active:
            categories_text.append(f"Otel Alt Kiralama: Otelin fatura maliyetlerinin %{sublet_pct}'i alt kiralama s\u00f6zle\u015fmesi gere\u011fi {sublet_name}'a aktar\u0131l\u0131r")
    else:
        elements.append(Paragraph("3. Categorii de Costuri", s_h2))
        categories_text = [
            "Electricitate, Apa, Gunoi - impartite intre toate companiile eligibile prin formula ponderata",
            "Gaz - impartit pe etaj (parter / etaj 1 / hotel) prin formula ponderata",
            f"Consumabile (ceai, cafea, apa) - impartite intre: {consumables_names}",
            f"Imprimanta - impartita egal intre: {printer_names}",
            f"Internet - impartit egal intre: {internet_names}",
            f"Intretinere - suma fixa EUR per companie, convertita la cursul EUR/RON ({eur_rate})",
            f"Chirie - suma fixa EUR per companie, convertita la cursul EUR/RON ({eur_rate})",
            "TVA 21% se aplica pe sumele de Intretinere si Chirie",
            "Sumele de consum extern sunt deduse din totalul facturilor inainte de alocare",
        ]
        if sublet_active:
            categories_text.append(f"Subinchiriere Hotel: {sublet_pct}% din costurile utilitatilor hotelului sunt alocate catre {sublet_name} conform acordului de subinchiriere")

    for item in categories_text:
        elements.append(Paragraph(f"\u2022  {item}", s_body))

    # ── COMPANY ELIGIBILITY ──
    if is_en:
        elements.append(Paragraph("4. Your Company's Eligibility", s_h2))
        elig_text = f"Based on your location ({company.get('building', '')} / {company.get('floor', '').replace('_', ' ').title()}), "
        elig_text += f"your company ({company['name']}) is eligible for the following cost categories:"
    elif is_tr:
        elements.append(Paragraph("4. Firmanizin Uygunlugu", s_h2))
        elig_text = f"Konumunuza gore ({company.get('building', '')} / {company.get('floor', '').replace('_', ' ').title()}), "
        elig_text += f"firmaniz ({company['name']}) asagidaki gider kategorileri icin uygundur:"
    else:
        elements.append(Paragraph("4. Eligibilitatea Companiei Dvs.", s_h2))
        elig_text = f"Pe baza locatiei dvs. ({company.get('building', '')} / {company.get('floor', '').replace('_', ' ').title()}), "
        elig_text += f"compania dvs. ({company['name']}) este eligibila pentru urmatoarele categorii de costuri:"
    elements.append(Paragraph(elig_text, s_body))

    elig_items = []
    if company.get("electricity_eligible"): elig_items.append("Electricity / Elektrik / Electricitate")
    if company.get("water_eligible"): elig_items.append("Water / Su / Apa")
    if company.get("garbage_eligible"): elig_items.append("Garbage / \u00c7\u00f6p / Gunoi")
    if company.get("has_heating"): elig_items.append("Gas / Do\u011falgaz / Gaz")
    if company.get("maintenance_rate_eur", 0) > 0:
        elig_items.append(f"Maintenance / Bak\u0131m / Intretinere ({company['maintenance_rate_eur']:.2f} EUR/month)")
    if company.get("monthly_rent_eur", 0) > 0:
        elig_items.append(f"Rent / Kira / Chirie ({company['monthly_rent_eur']:.2f} EUR/month)")
    for item in elig_items:
        elements.append(Paragraph(f"\u2022  {item}", s_body))

    elements.append(PageBreak())

    # ── PAGE 2: TERMS + SIGNATURE ──

    if is_en:
        elements.append(Paragraph("5. Monthly Process", s_h2))
        elements.append(Paragraph(
            "Each month, the Manager will calculate the cost allocation based on actual invoice amounts "
            "and distribute individual statements to each company. Payments are due within 15 days of "
            "receiving the monthly statement. Overpayments will be credited to the following month.", s_body))
        elements.append(Paragraph("6. Agreement", s_h2))
        elements.append(Paragraph(
            "By signing below, the undersigned confirms that they have read and understood the cost "
            "sharing methodology described above, and agree to participate in the shared cost allocation "
            "system of Premier Business Center.", s_body))
    elif is_tr:
        elements.append(Paragraph("5. Aylik Surec", s_h2))
        elements.append(Paragraph(
            "Her ay Yonetici, gercek fatura tutarlarina dayanarak maliyet dagitimini hesaplayacak ve "
            "her firmaya bireysel ekstre dagitacaktir. Odemeler aylik ekstrenin alinmasindan itibaren "
            "15 gun icinde yapilmalidir. Fazla odemeler bir sonraki aya alacak olarak aktarilacaktir.", s_body))
        elements.append(Paragraph("6. Sozlesme", s_h2))
        elements.append(Paragraph(
            "Asagida imza atan kisi, yukarida aciklanan maliyet paylasim yontemini okudugunu ve "
            "anladigini onaylar ve Premier Business Center'in ortak maliyet dagitim sistemine "
            "katilmayi kabul eder.", s_body))
    else:
        elements.append(Paragraph("5. Procesul Lunar", s_h2))
        elements.append(Paragraph(
            "In fiecare luna, Administratorul va calcula alocarea costurilor pe baza sumelor reale ale "
            "facturilor si va distribui extrase individuale fiecarei companii. Platile sunt scadente in "
            "termen de 15 zile de la primirea extrasului lunar. Supraplatile vor fi creditate in luna urmatoare.", s_body))
        elements.append(Paragraph("6. Acord", s_h2))
        elements.append(Paragraph(
            "Prin semnarea de mai jos, subsemnatul confirma ca a citit si inteles metodologia de partajare "
            "a costurilor descrisa mai sus si este de acord sa participe la sistemul de alocare a costurilor "
            "comune al Premier Business Center.", s_body))

    elements.append(Spacer(1, 5*mm))

    # Suggestions box
    if is_en:
        elements.append(Paragraph("Suggestions / Comments (if any):", s_sig_label))
    elif is_tr:
        elements.append(Paragraph("Oneriler / Yorumlar (varsa):", s_sig_label))
    else:
        elements.append(Paragraph("Sugestii / Comentarii (daca exista):", s_sig_label))

    box_data = [["", ""], ["", ""], ["", ""]]
    box_table = Table(box_data, colWidths=[CONTENT_W/2, CONTENT_W/2], rowHeights=[12*mm, 12*mm, 12*mm])
    box_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("BACKGROUND", (0, 0), (-1, -1), GRAY_BG),
    ]))
    elements.append(box_table)
    elements.append(Spacer(1, 8*mm))

    # Signature section
    if is_en:
        sig_labels = ["Company Name", "Authorized Person", "Signature", "Stamp", "Date"]
    elif is_tr:
        sig_labels = ["Firma Adi", "Yetkili Kisi", "Imza", "Kase", "Tarih"]
    else:
        sig_labels = ["Numele Companiei", "Persoana Autorizata", "Semnatura", "Stampila", "Data"]

    sig_data = []
    for lbl_text in sig_labels:
        sig_data.append([f"{lbl_text}:", ""])

    sig_table = Table(sig_data, colWidths=[45*mm, CONTENT_W - 45*mm], rowHeights=[14*mm]*len(sig_labels))
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (0, -1), GRAY_BG),
    ]))
    elements.append(sig_table)

    elements.append(Spacer(1, 8*mm))

    # Footer
    footer_text = "Premier Business Center \u2022 Bulevardul Mihail Kogalniceanu Nr. 12 \u2022 Sector 5, Bucuresti"
    elements.append(Paragraph(footer_text, ParagraphStyle("footer", fontName="Helvetica",
        fontSize=7, textColor=GRAY_LIGHT, alignment=TA_CENTER)))

    doc.build(elements)
    return filepath
