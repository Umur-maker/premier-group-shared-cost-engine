"""Generate user guide PDFs in English, Romanian, and Turkish."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image,
    PageBreak, ListFlowable, ListItem,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

NAVY = HexColor("#1a2d5a")
RED = HexColor("#e31e24")
GRAY = HexColor("#6b7280")
GRAY_LIGHT = HexColor("#9ca3af")
GRAY_BG = HexColor("#f9fafb")
GRAY_BORDER = HexColor("#e5e7eb")
WHITE = HexColor("#ffffff")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
LOGO_PATH = os.path.join(PROJECT_DIR, "backend", "core", "logo.png")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "user-guides")

PAGE_W = A4[0]
CONTENT_W = PAGE_W - 50 * mm


def get_styles():
    return {
        "cover_title": ParagraphStyle("ct", fontName="Helvetica-Bold", fontSize=28,
            textColor=NAVY, alignment=TA_CENTER, leading=34),
        "cover_sub": ParagraphStyle("cs", fontName="Helvetica", fontSize=14,
            textColor=RED, alignment=TA_CENTER, leading=18),
        "cover_ver": ParagraphStyle("cv", fontName="Helvetica", fontSize=10,
            textColor=GRAY_LIGHT, alignment=TA_CENTER, leading=14),
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18,
            textColor=NAVY, spaceBefore=12*mm, spaceAfter=4*mm, leading=22),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13,
            textColor=NAVY, spaceBefore=8*mm, spaceAfter=3*mm, leading=16),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=11,
            textColor=HexColor("#374151"), spaceBefore=5*mm, spaceAfter=2*mm, leading=14),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10,
            textColor=HexColor("#374151"), leading=14, spaceAfter=2*mm),
        "body_bold": ParagraphStyle("bb", fontName="Helvetica-Bold", fontSize=10,
            textColor=HexColor("#374151"), leading=14, spaceAfter=2*mm),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=10,
            textColor=HexColor("#374151"), leading=14, leftIndent=10*mm),
        "formula": ParagraphStyle("formula", fontName="Courier", fontSize=9,
            textColor=NAVY, leading=13, leftIndent=8*mm, spaceBefore=2*mm, spaceAfter=2*mm,
            backColor=GRAY_BG),
        "note": ParagraphStyle("note", fontName="Helvetica-Oblique", fontSize=9,
            textColor=GRAY, leading=12, spaceAfter=2*mm),
        "footer": ParagraphStyle("footer", fontName="Helvetica", fontSize=7,
            textColor=GRAY_LIGHT, alignment=TA_CENTER),
    }


CONTENT = {
    "en": {
        "lang_name": "English",
        "guide_title": "User Guide",
        "subtitle": "Shared Cost Allocation System",
        "version": "Version 2.0 - April 2026",
        "toc_title": "Table of Contents",
        "toc": [
            "1. System Overview",
            "2. Getting Started",
            "3. Monthly Input",
            "4. Companies Management",
            "5. Settings",
            "6. History & Reports",
            "7. Export Options",
            "8. Calculation Method",
        ],
        "sections": [
            # Section 1
            ("1. System Overview", [
                ("What is this system?", "body",
                 "The Premier Business Center Shared Cost Engine is an internal tool that fairly distributes "
                 "shared building costs (electricity, water, garbage, and gas) among all tenant companies. "
                 "Each month, the secretary enters the invoice totals and the system automatically calculates "
                 "how much each company owes based on their office area (m\u00b2) and number of persons."),
                ("Key Features", "h3", None),
                ("bullet_list", "bullets", [
                    "Monthly cost allocation across 13+ companies",
                    "Configurable allocation ratios (sqm % vs person %)",
                    "6 invoice types: Electricity, Water, Garbage, Hotel Gas, Ground Floor Gas, First Floor Gas",
                    "6 external usage deductions for outside parties",
                    "Internal Excel report with 3 detailed sheets",
                    "Company-specific PDF statement for each tenant",
                    "Run history with downloadable past reports",
                    "Bilingual support (English / Romanian)",
                    "Light and Dark mode",
                ]),
            ]),
            # Section 2
            ("2. Getting Started", [
                ("Accessing the System", "body",
                 "Open the application in your web browser. The interface consists of a sidebar navigation "
                 "on the left and the main content area on the right."),
                ("Navigation", "h3", None),
                ("bullet_list", "bullets", [
                    "Monthly Input - Enter invoice amounts and generate reports",
                    "Companies - View, add, edit company information",
                    "Settings - Configure allocation ratios, language, appearance",
                    "History - View and download past reports",
                ]),
            ]),
            # Section 3
            ("3. Monthly Input", [
                ("How to generate a monthly report", "body",
                 "This is the main page you will use each month."),
                ("Step by step:", "h3", None),
                ("bullet_list", "bullets", [
                    "Select the Month and Year",
                    "Enter the 6 invoice totals from the PDF bills (Electricity, Water, Garbage, Hotel Gas, Ground Floor Gas, First Floor Gas)",
                    "Enter any external usage amounts (for outside parties whose usage is deducted before allocation)",
                    "Click 'Generate Report'",
                    "Review the allocation preview table",
                    "Download the internal Excel report",
                    "Optionally download a PDF statement for a specific company",
                ]),
                ("Important notes:", "h3", None),
                ("bullet_list", "bullets", [
                    "All amounts are in Romanian Lei (RON)",
                    "You can use both comma and dot as decimal separator (e.g. 3.598,89 or 3598.89)",
                    "External usage cannot exceed the invoice total",
                    "The system validates all inputs before generating",
                ]),
            ]),
            # Section 4
            ("4. Companies Management", [
                ("Managing tenant companies", "body",
                 "The Companies page allows you to view all companies, add new ones, and edit existing ones."),
                ("Each company has:", "h3", None),
                ("bullet_list", "bullets", [
                    "Name, area (m\u00b2), number of persons",
                    "Building and floor location",
                    "Utility eligibility flags (heating, electricity, water, garbage)",
                    "Active/Inactive status",
                    "Optional: contact person, phone, email, office location, contract dates, notes",
                ]),
                ("Special rules:", "h3", None),
                ("bullet_list", "bullets", [
                    "Kolnberg - no gas heating (uses AC only)",
                    "Paul George Cata - no gas heating (uses AC only)",
                    "Hotel gas is charged 100% to the Hotel",
                    "Inactive companies are excluded from calculations but preserved in history",
                ]),
            ]),
            # Section 5
            ("5. Settings", [
                ("Configuring the system", "body",
                 "The Settings page has three sections:"),
                ("Allocation Ratios", "h3", None),
                ("ratio_desc", "body",
                 "For each expense type, you set the sqm % (area weight). The person % is automatically "
                 "calculated as 100 - sqm %. This determines how costs are split between area-based and "
                 "person-based allocation."),
                ("table", "ratio_table", [
                    ["Expense Type", "sqm %", "person %", "Logic"],
                    ["Electricity", "50%", "50%", "Equal weight: AC (area) + devices (person)"],
                    ["Gas", "80%", "20%", "Heating is mostly area-based"],
                    ["Water", "30%", "70%", "Mostly per-person consumption"],
                    ["Garbage", "25%", "75%", "People generate garbage"],
                ]),
                ("Language", "h3", None),
                ("lang_desc", "body",
                 "Choose between English and Romanian. This affects all UI labels and Excel/PDF export language."),
                ("Appearance", "h3", None),
                ("theme_desc", "body",
                 "Choose Light or Dark mode. Your preference is saved automatically."),
            ]),
            # Section 6
            ("6. History & Reports", [
                ("Run History", "body",
                 "Every time you generate a report, it is automatically saved to the history. "
                 "Each history entry stores a complete snapshot of the calculation including all company data, "
                 "ratios, and results at that point in time."),
                ("What you can do:", "h3", None),
                ("bullet_list", "bullets", [
                    "Download the internal Excel report for any past month",
                    "Generate a company-specific PDF statement from any past run",
                    "Delete old runs you no longer need",
                ]),
                ("Snapshot guarantee:", "h3", None),
                ("snapshot_desc", "body",
                 "Historical reports use the data from when they were generated. If you change company data "
                 "or ratios later, past reports remain unchanged. February's report will always show February's numbers."),
            ]),
            # Section 7
            ("7. Export Options", [
                ("Two export types are available:", "body", None),
                ("1. Internal Report (Excel)", "h3", None),
                ("internal_desc", "body",
                 "A 3-sheet Excel workbook for internal use:\n"
                 "- Summary: each company's total payment\n"
                 "- Detailed Breakdown: amounts per expense category\n"
                 "- Calculation Details: inputs, ratios, eligible companies, and allocation logic"),
                ("2. Company Statement (PDF)", "h3", None),
                ("stmt_desc", "body",
                 "A professional PDF document for one specific company, suitable for sending directly to the tenant. "
                 "Includes company name, expense breakdown, total amount due, and an explanatory note about the "
                 "cost sharing methodology. Branded with the Premier Business Center logo."),
            ]),
            # Section 8
            ("8. Calculation Method", [
                ("Overview", "body",
                 "The system uses a weighted formula combining office area (m\u00b2) and number of persons to "
                 "determine each company's fair share of each expense."),
                ("Formula", "h3", None),
                ("formula_text", "formula",
                 "company_share = net_amount x (sqm_weight x sqm_ratio + person_weight x person_ratio)"),
                ("Where:", "h3", None),
                ("bullet_list", "bullets", [
                    "net_amount = invoice total - external usage",
                    "sqm_ratio = company's m\u00b2 / total eligible m\u00b2",
                    "person_ratio = company's persons / total eligible persons",
                    "sqm_weight + person_weight = 100%",
                ]),
                ("Example: Balkan's Electricity", "h3", None),
                ("example", "body",
                 "Balkan has 25.5 m\u00b2 and 2 persons.\n"
                 "Total eligible: 623.29 m\u00b2 and 33 persons.\n"
                 "Electricity ratio: 50% sqm + 50% person.\n"
                 "Electricity bill: 3,598.89 RON."),
                ("calc_formula", "formula",
                 "sqm_ratio    = 25.5 / 623.29 = 4.09%\n"
                 "person_ratio = 2 / 33        = 6.06%\n"
                 "share = 3,598.89 x (0.50 x 0.0409 + 0.50 x 0.0606)\n"
                 "      = 3,598.89 x 0.0508\n"
                 "      = 182.82 RON"),
                ("Gas allocation rules:", "h3", None),
                ("bullet_list", "bullets", [
                    "Hotel gas: 100% charged to Hotel only",
                    "Ground floor gas: split among ground floor companies with heating (excludes Kolnberg)",
                    "First floor gas: split among first floor companies with heating (excludes Paul George Cata)",
                ]),
                ("Rounding:", "h3", None),
                ("rounding_desc", "body",
                 "All amounts are rounded to 2 decimal places. To ensure the sum of all company shares exactly "
                 "equals the net amount (no missing or extra cents), any rounding difference is applied to the "
                 "largest share."),
            ]),
        ],
    },
    "ro": {
        "lang_name": "Romanian",
        "guide_title": "Ghid de Utilizare",
        "subtitle": "Sistem de Alocare a Costurilor Comune",
        "version": "Versiunea 2.0 - Aprilie 2026",
        "toc_title": "Cuprins",
        "toc": [
            "1. Prezentare Generala",
            "2. Primii Pasi",
            "3. Date Lunare",
            "4. Administrare Companii",
            "5. Setari",
            "6. Istoric si Rapoarte",
            "7. Optiuni de Export",
            "8. Metoda de Calcul",
        ],
        "sections": [
            ("1. Prezentare Generala", [
                ("Ce este acest sistem?", "body",
                 "Premier Business Center Shared Cost Engine este un instrument intern care distribuie in mod echitabil "
                 "costurile comune ale cladirii (electricitate, apa, gunoi si gaz) intre toate companiile chiriase. "
                 "In fiecare luna, secretara introduce totalurile facturilor, iar sistemul calculeaza automat "
                 "cat datoreaza fiecare companie pe baza suprafetei biroului (m\u00b2) si a numarului de persoane."),
                ("Functionalitati principale", "h3", None),
                ("bullet_list", "bullets", [
                    "Alocare lunara a costurilor pentru 13+ companii",
                    "Proportii configurabile (mp % vs persoane %)",
                    "6 tipuri de facturi: Electricitate, Apa, Gunoi, Gaz Hotel, Gaz Parter, Gaz Etaj 1",
                    "6 deduceri pentru consum extern",
                    "Raport intern Excel cu 3 foi detaliate",
                    "Extras PDF individual pentru fiecare chirias",
                    "Istoric cu rapoarte descarcabile",
                    "Suport bilingv (Engleza / Romana)",
                    "Mod Luminos si Inchis",
                ]),
            ]),
            ("2. Primii Pasi", [
                ("Accesarea sistemului", "body",
                 "Deschideti aplicatia in browserul web. Interfata contine o bara de navigare in stanga "
                 "si zona principala de continut in dreapta."),
                ("Navigare", "h3", None),
                ("bullet_list", "bullets", [
                    "Date Lunare - Introduceti sumele facturilor si generati rapoarte",
                    "Companii - Vizualizati, adaugati, editati informatiile companiilor",
                    "Setari - Configurati proportiile de alocare, limba, aspectul",
                    "Istoric - Vizualizati si descarcati rapoartele anterioare",
                ]),
            ]),
            ("3. Date Lunare", [
                ("Cum se genereaza un raport lunar", "body",
                 "Aceasta este pagina principala pe care o veti folosi in fiecare luna."),
                ("Pas cu pas:", "h3", None),
                ("bullet_list", "bullets", [
                    "Selectati Luna si Anul",
                    "Introduceti cele 6 totaluri ale facturilor (Electricitate, Apa, Gunoi, Gaz Hotel, Gaz Parter, Gaz Etaj 1)",
                    "Introduceti sumele de consum extern (pentru partile externe al caror consum se deduce inainte de alocare)",
                    "Apasati 'Genereaza Raport'",
                    "Verificati tabelul de previzualizare a alocarii",
                    "Descarcati raportul intern Excel",
                    "Optional, descarcati un extras PDF pentru o companie specifica",
                ]),
                ("Note importante:", "h3", None),
                ("bullet_list", "bullets", [
                    "Toate sumele sunt in Lei Romanesti (RON)",
                    "Puteti folosi atat virgula cat si punctul ca separator zecimal (ex. 3.598,89 sau 3598.89)",
                    "Consumul extern nu poate depasi totalul facturii",
                    "Sistemul valideaza toate datele inainte de generare",
                ]),
            ]),
            ("4. Administrare Companii", [
                ("Administrarea companiilor chiriase", "body",
                 "Pagina Companii va permite sa vizualizati toate companiile, sa adaugati altele noi si sa le editati pe cele existente."),
                ("Fiecare companie are:", "h3", None),
                ("bullet_list", "bullets", [
                    "Nume, suprafata (m\u00b2), numar de persoane",
                    "Cladire si etaj",
                    "Eligibilitate utilitati (incalzire, electricitate, apa, gunoi)",
                    "Stare Activ/Inactiv",
                    "Optional: persoana de contact, telefon, email, locatie birou, date contract, notite",
                ]),
                ("Reguli speciale:", "h3", None),
                ("bullet_list", "bullets", [
                    "Kolnberg - fara incalzire cu gaz (foloseste doar AC)",
                    "Paul George Cata - fara incalzire cu gaz (foloseste doar AC)",
                    "Gazul hotelului se factureaza 100% Hotelului",
                    "Companiile inactive sunt excluse din calcule dar pastrate in istoric",
                ]),
            ]),
            ("5. Setari", [
                ("Configurarea sistemului", "body", "Pagina Setari are trei sectiuni:"),
                ("Proportii de Alocare", "h3", None),
                ("ratio_desc", "body",
                 "Pentru fiecare tip de cheltuiala, setati procentul mp (ponderea suprafetei). Procentul persoane "
                 "se calculeaza automat ca 100 - mp %. Acest lucru determina cum se impart costurile intre "
                 "alocarea bazata pe suprafata si cea bazata pe persoane."),
                ("table", "ratio_table", [
                    ["Tip Cheltuiala", "mp %", "persoane %", "Logica"],
                    ["Electricitate", "50%", "50%", "Pondere egala: AC (suprafata) + dispozitive (persoana)"],
                    ["Gaz", "80%", "20%", "Incalzirea depinde majoritar de suprafata"],
                    ["Apa", "30%", "70%", "Majoritar consum per persoana"],
                    ["Gunoi", "25%", "75%", "Persoanele genereaza gunoi"],
                ]),
                ("Limba", "h3", None),
                ("lang_desc", "body", "Alegeti intre Engleza si Romana. Afecteaza toate etichetele UI si limba rapoartelor."),
                ("Aspect", "h3", None),
                ("theme_desc", "body", "Alegeti modul Luminos sau Inchis. Preferinta se salveaza automat."),
            ]),
            ("6. Istoric si Rapoarte", [
                ("Istoric Rapoarte", "body",
                 "De fiecare data cand generati un raport, acesta se salveaza automat in istoric. "
                 "Fiecare intrare stocheaza un snapshot complet al calculului."),
                ("Ce puteti face:", "h3", None),
                ("bullet_list", "bullets", [
                    "Descarcati raportul intern Excel pentru orice luna anterioara",
                    "Generati un extras PDF pentru o companie din orice raport anterior",
                    "Stergeti rapoartele vechi de care nu mai aveti nevoie",
                ]),
                ("Garantia snapshot:", "h3", None),
                ("snapshot_desc", "body",
                 "Rapoartele istorice folosesc datele de la momentul generarii. Daca modificati datele companiei "
                 "sau proportiile ulterior, rapoartele anterioare raman neschimbate."),
            ]),
            ("7. Optiuni de Export", [
                ("Doua tipuri de export sunt disponibile:", "body", None),
                ("1. Raport Intern (Excel)", "h3", None),
                ("internal_desc", "body",
                 "Un fisier Excel cu 3 foi:\n"
                 "- Sumar: plata totala a fiecarei companii\n"
                 "- Detalii pe Categorii: sume pe fiecare tip de cheltuiala\n"
                 "- Detalii Calcul: date introduse, proportii, companii eligibile si logica de alocare"),
                ("2. Extras Companie (PDF)", "h3", None),
                ("stmt_desc", "body",
                 "Un document PDF profesional pentru o companie specifica, potrivit pentru trimiterea directa catre chirias. "
                 "Include numele companiei, defalcarea cheltuielilor, suma totala de plata si o nota explicativa."),
            ]),
            ("8. Metoda de Calcul", [
                ("Prezentare generala", "body",
                 "Sistemul foloseste o formula ponderata care combina suprafata biroului (m\u00b2) si numarul "
                 "de persoane pentru a determina cota echitabila a fiecarei companii."),
                ("Formula", "h3", None),
                ("formula_text", "formula",
                 "cota_companie = suma_neta x (pondere_mp x raport_mp + pondere_pers x raport_pers)"),
                ("Unde:", "h3", None),
                ("bullet_list", "bullets", [
                    "suma_neta = total factura - consum extern",
                    "raport_mp = m\u00b2 companie / total m\u00b2 eligibil",
                    "raport_pers = persoane companie / total persoane eligibile",
                    "pondere_mp + pondere_pers = 100%",
                ]),
                ("Exemplu: Electricitatea Balkan", "h3", None),
                ("example", "body",
                 "Balkan are 25,5 m\u00b2 si 2 persoane.\n"
                 "Total eligibil: 623,29 m\u00b2 si 33 persoane.\n"
                 "Proportie electricitate: 50% mp + 50% persoane.\n"
                 "Factura electricitate: 3.598,89 RON."),
                ("calc_formula", "formula",
                 "raport_mp    = 25,5 / 623,29 = 4,09%\n"
                 "raport_pers  = 2 / 33        = 6,06%\n"
                 "cota = 3.598,89 x (0,50 x 0,0409 + 0,50 x 0,0606)\n"
                 "     = 3.598,89 x 0,0508\n"
                 "     = 182,82 RON"),
                ("Reguli alocare gaz:", "h3", None),
                ("bullet_list", "bullets", [
                    "Gaz hotel: 100% facturat Hotelului",
                    "Gaz parter: impartit intre companiile de la parter cu incalzire (fara Kolnberg)",
                    "Gaz etaj 1: impartit intre companiile de la etaj 1 cu incalzire (fara Paul George Cata)",
                ]),
                ("Rotunjire:", "h3", None),
                ("rounding_desc", "body",
                 "Toate sumele sunt rotunjite la 2 zecimale. Pentru a asigura ca suma cotelor este exact egala "
                 "cu suma neta, orice diferenta de rotunjire se aplica celei mai mari cote."),
            ]),
        ],
    },
    "tr": {
        "lang_name": "Turkish",
        "guide_title": "Kullanim Kilavuzu",
        "subtitle": "Ortak Maliyet Dagitim Sistemi",
        "version": "Surum 2.0 - Nisan 2026",
        "toc_title": "Icindekiler",
        "toc": [
            "1. Sistem Genel Bakis",
            "2. Baslarken",
            "3. Aylik Veri Girisi",
            "4. Firma Yonetimi",
            "5. Ayarlar",
            "6. Gecmis ve Raporlar",
            "7. Cikti Secenekleri",
            "8. Hesaplama Yontemi",
        ],
        "sections": [
            ("1. Sistem Genel Bakis", [
                ("Bu sistem nedir?", "body",
                 "Premier Business Center Ortak Maliyet Motoru, bina ortak giderlerini (elektrik, su, cop ve dogalgaz) "
                 "tum kiracilara adil sekilde dagitan bir ic aractir. Her ay sekreter fatura toplamlarini girer "
                 "ve sistem, her firmanin ofis alani (m\u00b2) ve kisi sayisina gore ne kadar odeyecegini otomatik hesaplar."),
                ("Temel Ozellikler", "h3", None),
                ("bullet_list", "bullets", [
                    "13+ firma icin aylik maliyet dagitimi",
                    "Yapilandirilabilir dagitim oranlari (m\u00b2 % vs kisi %)",
                    "6 fatura tipi: Elektrik, Su, Cop, Otel Dogalgaz, Zemin Kat Dogalgaz, 1. Kat Dogalgaz",
                    "6 dis kullanim dusumu",
                    "3 sayfali ic Excel raporu",
                    "Her kiraciya ozel PDF ekstre",
                    "Indirilebilir gecmis raporlar",
                    "Iki dil destegi (Ingilizce / Rumence)",
                    "Acik ve Koyu mod",
                ]),
            ]),
            ("2. Baslarken", [
                ("Sisteme erisim", "body",
                 "Uygulamayi web tarayicinizda acin. Arayuz, solda bir navigasyon cubugu ve sagda "
                 "ana icerik alanindan olusur."),
                ("Navigasyon", "h3", None),
                ("bullet_list", "bullets", [
                    "Aylik Giris - Fatura tutarlarini girin ve rapor olusturun",
                    "Firmalar - Firma bilgilerini goruntuleyip duzenleyin",
                    "Ayarlar - Dagitim oranlarini, dili, gorunumu yapilandirin",
                    "Gecmis - Onceki raporlari goruntuleyip indirin",
                ]),
            ]),
            ("3. Aylik Veri Girisi", [
                ("Aylik rapor nasil olusturulur", "body",
                 "Bu, her ay kullanacaginiz ana sayfadir."),
                ("Adim adim:", "h3", None),
                ("bullet_list", "bullets", [
                    "Ay ve Yili secin",
                    "PDF faturalardan 6 fatura toplamini girin (Elektrik, Su, Cop, Otel Gaz, Zemin Kat Gaz, 1. Kat Gaz)",
                    "Varsa dis kullanim tutarlarini girin (dagitim oncesi dusulecek dis taraf kullanimlari)",
                    "'Rapor Olustur' tusuna basin",
                    "Dagitim on izleme tablosunu inceleyin",
                    "Ic Excel raporunu indirin",
                    "Istege bagli olarak belirli bir firma icin PDF ekstre indirin",
                ]),
                ("Onemli notlar:", "h3", None),
                ("bullet_list", "bullets", [
                    "Tum tutarlar Rumen Leyi (RON) cinsindendir",
                    "Ondalik ayirici olarak hem virgul hem nokta kullanabilirsiniz (ornegin 3.598,89 veya 3598.89)",
                    "Dis kullanim fatura toplamini asamaz",
                    "Sistem olusturmadan once tum girileri dogrular",
                ]),
            ]),
            ("4. Firma Yonetimi", [
                ("Kiraci firmalarin yonetimi", "body",
                 "Firmalar sayfasi tum firmalari goruntulemenize, yenilerini eklemenize ve mevcutlari duzenlemenize olanak tanir."),
                ("Her firmanin bilgileri:", "h3", None),
                ("bullet_list", "bullets", [
                    "Ad, alan (m\u00b2), kisi sayisi",
                    "Bina ve kat konumu",
                    "Hizmet uygunluk bayraklari (isitma, elektrik, su, cop)",
                    "Aktif/Pasif durumu",
                    "Opsiyonel: irtibat kisisi, telefon, e-posta, ofis konumu, sozlesme tarihleri, notlar",
                ]),
                ("Ozel kurallar:", "h3", None),
                ("bullet_list", "bullets", [
                    "Kolnberg - dogalgaz isitmasi yok (sadece klima kullaniyor)",
                    "Paul George Cata - dogalgaz isitmasi yok (sadece klima kullaniyor)",
                    "Otel dogalgazi %100 Otel'e fatura edilir",
                    "Pasif firmalar hesaplamalardan cikarilir ancak gecmiste korunur",
                ]),
            ]),
            ("5. Ayarlar", [
                ("Sistemi yapilandirma", "body", "Ayarlar sayfasi uc bolumden olusur:"),
                ("Dagitim Oranlari", "h3", None),
                ("ratio_desc", "body",
                 "Her gider tipi icin m\u00b2 % (alan agirligi) belirlersiniz. Kisi % otomatik olarak 100 - m\u00b2 % "
                 "seklinde hesaplanir. Bu, maliyetlerin alan bazli ve kisi bazli dagitim arasindaki dengesini belirler."),
                ("table", "ratio_table", [
                    ["Gider Tipi", "m\u00b2 %", "kisi %", "Mantik"],
                    ["Elektrik", "%50", "%50", "Esit agirlik: klima (alan) + cihazlar (kisi)"],
                    ["Dogalgaz", "%80", "%20", "Isitma buyuk olcude alana baglidir"],
                    ["Su", "%30", "%70", "Cogunlukla kisi bazli tuketim"],
                    ["Cop", "%25", "%75", "Insanlar cop uretir"],
                ]),
                ("Dil", "h3", None),
                ("lang_desc", "body", "Ingilizce ve Rumence arasinda secim yapin. Tum arayuz etiketlerini ve rapor dilini etkiler."),
                ("Gorunum", "h3", None),
                ("theme_desc", "body", "Acik veya Koyu modu secin. Tercihiniz otomatik kaydedilir."),
            ]),
            ("6. Gecmis ve Raporlar", [
                ("Rapor Gecmisi", "body",
                 "Her rapor olusturdugunuzda otomatik olarak gecmise kaydedilir. "
                 "Her gecmis kaydi, hesaplamanin tam bir anlk goruntusunu saklar."),
                ("Yapabilecekleriniz:", "h3", None),
                ("bullet_list", "bullets", [
                    "Herhangi bir onceki ay icin ic Excel raporunu indirin",
                    "Herhangi bir onceki rapordan bir firma icin PDF ekstre olusturun",
                    "Artik ihtiyaciniz olmayan eski raporlari silin",
                ]),
                ("Anlik goruntu garantisi:", "h3", None),
                ("snapshot_desc", "body",
                 "Gecmis raporlar, olusturuldugu andaki verileri kullanir. Daha sonra firma verilerini "
                 "veya oranlari degistirseniz bile, onceki raporlar degismez."),
            ]),
            ("7. Cikti Secenekleri", [
                ("Iki cikti tipi mevcuttur:", "body", None),
                ("1. Ic Rapor (Excel)", "h3", None),
                ("internal_desc", "body",
                 "3 sayfali bir Excel dosyasi:\n"
                 "- Ozet: her firmanin toplam odemesi\n"
                 "- Ayrintili Kirilim: gider kategorisine gore tutarlar\n"
                 "- Hesaplama Detaylari: girisler, oranlar, uygun firmalar ve dagitim mantigi"),
                ("2. Firma Ekstresi (PDF)", "h3", None),
                ("stmt_desc", "body",
                 "Belirli bir firma icin profesyonel bir PDF belgesi, dogrudan kiraciya gondermek icin uygundur. "
                 "Firma adi, gider dokumu, odenecek toplam tutar ve maliyet paylasim yontemi hakkinda aciklayici bir not icerir."),
            ]),
            ("8. Hesaplama Yontemi", [
                ("Genel bakis", "body",
                 "Sistem, her firmanin adil payini belirlemek icin ofis alani (m\u00b2) ve kisi sayisini "
                 "birlestiren agirlikli bir formul kullanir."),
                ("Formul", "h3", None),
                ("formula_text", "formula",
                 "firma_payi = net_tutar x (alan_agirligi x alan_orani + kisi_agirligi x kisi_orani)"),
                ("Aciklama:", "h3", None),
                ("bullet_list", "bullets", [
                    "net_tutar = fatura toplami - dis kullanim",
                    "alan_orani = firmanin m\u00b2'si / toplam uygun m\u00b2",
                    "kisi_orani = firmanin kisileri / toplam uygun kisiler",
                    "alan_agirligi + kisi_agirligi = %100",
                ]),
                ("Ornek: Balkan'in Elektrik Payi", "h3", None),
                ("example", "body",
                 "Balkan 25,5 m\u00b2 ve 2 kisiye sahiptir.\n"
                 "Toplam uygun: 623,29 m\u00b2 ve 33 kisi.\n"
                 "Elektrik orani: %50 alan + %50 kisi.\n"
                 "Elektrik faturasi: 3.598,89 RON."),
                ("calc_formula", "formula",
                 "alan_orani  = 25,5 / 623,29 = %4,09\n"
                 "kisi_orani  = 2 / 33        = %6,06\n"
                 "pay = 3.598,89 x (0,50 x 0,0409 + 0,50 x 0,0606)\n"
                 "    = 3.598,89 x 0,0508\n"
                 "    = 182,82 RON"),
                ("Dogalgaz dagitim kurallari:", "h3", None),
                ("bullet_list", "bullets", [
                    "Otel dogalgazi: %100 Otel'e fatura edilir",
                    "Zemin kat dogalgazi: isitmali zemin kat firmalari arasinda paylasilir (Kolnberg haric)",
                    "1. kat dogalgazi: isitmali 1. kat firmalari arasinda paylasilir (Paul George Cata haric)",
                ]),
                ("Yuvarlama:", "h3", None),
                ("rounding_desc", "body",
                 "Tum tutarlar 2 ondalik basamaga yuvarlanir. Firma paylarinin toplaminin net tutara tam olarak "
                 "esit olmasini saglamak icin, yuvarlama farki en buyuk paya uygulanir."),
            ]),
        ],
    },
}


def build_pdf(lang_key):
    content = CONTENT[lang_key]
    styles = get_styles()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, f"User_Guide_{content['lang_name']}.pdf")

    doc = SimpleDocTemplate(filepath, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm, topMargin=20*mm, bottomMargin=20*mm)

    elements = []

    # ── COVER PAGE ──
    elements.append(Spacer(1, 30*mm))

    if os.path.exists(LOGO_PATH):
        img_reader = ImageReader(LOGO_PATH)
        iw, ih = img_reader.getSize()
        logo_w = 80 * mm
        logo_h = logo_w * (ih / iw)
        logo = Image(LOGO_PATH, width=logo_w, height=logo_h)
        logo.hAlign = "CENTER"
        elements.append(logo)

    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(content["guide_title"], styles["cover_title"]))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(content["subtitle"], styles["cover_sub"]))
    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(content["version"], styles["cover_ver"]))

    elements.append(PageBreak())

    # ── TABLE OF CONTENTS ──
    elements.append(Paragraph(content["toc_title"], styles["h1"]))
    for item in content["toc"]:
        elements.append(Paragraph(item, styles["body"]))
    elements.append(PageBreak())

    # ── SECTIONS ──
    for section_title, items in content["sections"]:
        elements.append(Paragraph(section_title, styles["h1"]))

        for item in items:
            name, style_key, value = item

            if style_key == "h3":
                elements.append(Paragraph(name, styles["h3"]))
            elif style_key == "body" and value:
                for line in value.split("\n"):
                    elements.append(Paragraph(line, styles["body"]))
            elif style_key == "formula" and value:
                for line in value.split("\n"):
                    elements.append(Paragraph(line, styles["formula"]))
            elif style_key == "bullets" and value:
                for bullet in value:
                    elements.append(Paragraph(f"\u2022  {bullet}", styles["bullet"]))
                elements.append(Spacer(1, 2*mm))
            elif style_key == "ratio_table" and value:
                table = Table(value, colWidths=[35*mm, 18*mm, 22*mm, CONTENT_W - 75*mm])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (2, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.3, GRAY_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_BG]),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 3*mm))

    doc.build(elements)
    print(f"  Generated: {filepath}")
    return filepath


if __name__ == "__main__":
    print("Generating user guides...")
    for lang in ("en", "ro", "tr"):
        build_pdf(lang)
    print("Done!")
