#!/usr/bin/env python3
"""
Builds the French, Spanish and Hebrew versions of the website from the English pages:

    docs/index.html    -> docs/fr/index.html, docs/es/index.html, docs/he/index.html
    docs/license.html  -> docs/fr/license.html, docs/es/license.html, docs/he/license.html

The English pages are the source: edit them, then run `python3 .github/scripts/build-site.py`.
Every text on the English landing page must have a translation below (or be listed in KEEP); a
text without one stops the build and is printed, so a translated page never silently shows
English or an old sentence. Amounts follow each language's currency and format ($, euro, shekel).

The license pages carry a translated summary; the English terms stay the binding text.
Standard library only.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

# Texts that stay as they are in every language: product and service names, code, addresses.
KEEP = {
    "Refund-Me", "SSO", "Excel · CSV · PDF", "PostgreSQL", "Cloudflare R2", "Amazon S3, MinIO, Wasabi",
    "Microsoft SQL Server", "MySQL / MariaDB", "Google Workspace", "Entra ID", "Workspace",
    "waiting_for_me", "approve_month", "https://expenses.your-company.com/setup", "smtp.acme.example",
    "logo.svg", "INSTALL.md", "GitHub", "http://your-server:3855", "Microsoft (Entra ID)",
    "curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/install.sh | sh",
    "cd refund-me && docker compose pull && docker compose up -d", "Excel, CSV, PDF",
    "Language: English",  # the switcher, rebuilt per language
    "Excel", "CSV", "PDF",
}

FLAGS = {
    "en": '<svg class="flag" viewBox="0 0 60 42" aria-hidden="true"><rect width="60" height="42" fill="#012169"/><path d="M0 0l60 42M60 0L0 42" stroke="#fff" stroke-width="9"/><path d="M0 0l60 42M60 0L0 42" stroke="#C8102E" stroke-width="3"/><path d="M30 0v42M0 21h60" stroke="#fff" stroke-width="14"/><path d="M30 0v42M0 21h60" stroke="#C8102E" stroke-width="8"/></svg>',
    "fr": '<svg class="flag" viewBox="0 0 3 2" aria-hidden="true"><rect width="1" height="2" fill="#002654"/><rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#CE1126"/></svg>',
    "es": '<svg class="flag" viewBox="0 0 3 2" aria-hidden="true"><rect width="3" height="2" fill="#AA151B"/><rect y=".5" width="3" height="1" fill="#F1BF00"/></svg>',
    "he": '<svg class="flag" viewBox="0 0 220 160" aria-hidden="true"><rect width="220" height="160" fill="#fff"/><rect y="15" width="220" height="25" fill="#0038b8"/><rect y="120" width="220" height="25" fill="#0038b8"/><path d="M110 52l24 42h-48zM110 108l-24-42h48z" fill="none" stroke="#0038b8" stroke-width="5.5"/></svg>',
}
ORDER = ["en", "fr", "es", "he"]
# Each page names the languages in its own language (the English page stays English only).
NAMES = {
    "en": {"en": "English", "fr": "French", "es": "Spanish", "he": "Hebrew", "label": "Language: English"},
    "fr": {"en": "Anglais", "fr": "Français", "es": "Espagnol", "he": "Hébreu", "label": "Langue : français"},
    "es": {"en": "Inglés", "fr": "Francés", "es": "Español", "he": "Hebreo", "label": "Idioma: español"},
    "he": {"en": "אנגלית", "fr": "צרפתית", "es": "ספרדית", "he": "עברית", "label": "שפה: עברית"},
}
MARK = {"fr": "€", "es": "€", "he": "₪"}


def switcher(lang: str, page: str) -> str:
    """The language menu for a page ("index.html" or "license.html") in `lang`."""
    up = "" if lang == "en" else "../"

    def href(target: str) -> str:
        folder = "" if target == "en" else f"{target}/"
        return f"{up}{folder}{'' if page == 'index.html' else page}" or "./"

    current = ' aria-current="true"'
    items = "\n".join(
        f'        <li><a href="{href(t)}" hreflang="{t}"{current if t == lang else ""}>{FLAGS[t]}{NAMES[lang][t]}</a></li>'
        for t in ORDER
    )
    chev = '<svg class="chev" viewBox="0 0 10 10" aria-hidden="true"><path d="M2 3.5l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
    return (
        f'<div class="lang">\n      <button type="button" class="lang-btn" aria-expanded="false" aria-controls="lang-menu" '
        f'aria-label="{NAMES[lang]["label"]}">{FLAGS[lang]}<span>{lang.upper()}</span>{chev}</button>\n'
        f'      <ul class="lang-menu" id="lang-menu" hidden>\n{items}\n      </ul>\n    </div>'
    )


def fr_typo(s: str) -> str:
    """French spacing: a narrow no-break space before ? ! ; and a no-break space before :."""
    s = re.sub(r" ([?!;])", " \\1", s)
    s = re.sub(r" :", " :", s)
    return s.replace("« ", "« ").replace(" »", " »")


# Amounts and receipt figures, per language.
MONEY = {
    "fr": {"$1,284.60": "1 284,60 €", "$28.45": "28,45 €", "$186.50": "186,50 €", "$412.00": "412,00 €",
           "118.00": "118,00", "40.05": "40,05", "28.45": "28,45", "186.50": "186,50"},
    "es": {"$1,284.60": "1.284,60 €", "$28.45": "28,45 €", "$186.50": "186,50 €", "$412.00": "412,00 €",
           "118.00": "118,00", "40.05": "40,05", "28.45": "28,45", "186.50": "186,50"},
    "he": {"$1,284.60": "₪1,284.60", "$28.45": "₪28.45", "$186.50": "₪186.50", "$412.00": "₪412.00"},
}

T = {"fr": {}, "es": {}, "he": {}}


def add(en, fr, es, he):
    T["fr"][en] = fr_typo(fr)
    T["es"][en] = es
    # Hebrew typography uses straight double quotes for speech.
    T["he"][en] = he.replace("\u201c", '"').replace("\u201d", '"')


# --- The landing page --------------------------------------------------------------------------
add("Expense reimbursement for Israeli companies: snap receipts on the phone, approve with a tap, export to accounting. On your own server, in Hebrew, English, French and Spanish.", "Remboursement de notes de frais pour les entreprises israéliennes : photographiez les reçus, approuvez d'un geste, exportez vers la comptabilité. Sur votre propre serveur, en hébreu, anglais, français et espagnol.", "Reembolso de gastos para empresas israelíes: fotografía los tickets, aprueba con un toque y exporta a contabilidad. En tu propio servidor, en hebreo, inglés, francés y español.", "החזר הוצאות לחברות בישראל: מצלמים קבלות בטלפון, מאשרים בנגיעה, מייצאים להנהלת החשבונות. על השרת שלכם, בעברית, אנגלית, צרפתית וספרדית.")
add("Sections", "Sections", "Secciones", "חלקים")
add("How it works", "Fonctionnement", "Cómo funciona", "איך זה עובד")
add("Devices", "Appareils", "Dispositivos", "מכשירים")
add("AI assistants", "Assistants IA", "Asistentes de IA", "עוזרי AI")
add("Security", "Sécurité", "Seguridad", "אבטחה")
add("Controls", "Contrôles", "Controles", "בקרות")
add("Install", "Installer", "Instalar", "התקנה")
add("License", "Licence", "Licencia", "רישיון")
add("Get started", "Commencer", "Empezar", "להתחיל")
add("Expense reimbursement · 4 languages", "Notes de frais · 4 langues", "Reembolso de gastos · 4 idiomas", "החזר הוצאות · 4 שפות")
add("Snap the receipt.", "Photographiez le reçu.", "Fotografía el ticket.", "מצלמים את הקבלה.")
add("Get paid back.", "Soyez remboursé.", "Recupera tu dinero.", "מקבלים החזר.")
add("Employees photograph receipts on their phone. Refund-Me reads them, managers and accounting approve with a tap, and the month lands in your accounting system. On your own server, so your data never leaves the company.",
    "Les employés photographient leurs reçus avec leur téléphone. Refund-Me les lit, les managers et la comptabilité approuvent d'un geste, et le mois arrive dans votre logiciel comptable. Sur votre propre serveur : vos données ne quittent jamais l'entreprise.",
    "Los empleados fotografían sus tickets con el móvil. Refund-Me los lee, los responsables y contabilidad aprueban con un toque, y el mes llega a tu sistema contable. En tu propio servidor, así que tus datos nunca salen de la empresa.",
    "העובדים מצלמים קבלות בטלפון. Refund-Me קורא אותן, המנהלים והנהלת החשבונות מאשרים בנגיעה, והחודש מגיע למערכת הנהלת החשבונות שלכם. על השרת שלכם, כך שהמידע לא יוצא מהחברה.")
add("Install on your server", "Installer sur votre serveur", "Instalar en tu servidor", "התקנה על השרת שלכם")
add("See how it works", "Voir comment ça marche", "Ver cómo funciona", "לראות איך זה עובד")
add("Phone, tablet & computer", "Téléphone, tablette et ordinateur", "Móvil, tableta y ordenador", "טלפון, טאבלט ומחשב")
add("Microsoft & Google sign-in", "Connexion Microsoft et Google", "Acceso con Microsoft y Google", "כניסה עם Microsoft ו-Google")
add("Reads receipts in 4 languages", "Lit les reçus en 4 langues", "Lee tickets en 4 idiomas", "קורא קבלות ב-4 שפות")
add("Any currency, converted", "Toutes devises, converties", "Cualquier moneda, convertida", "כל מטבע, בהמרה")
add("Works with AI assistants", "Compatible avec les assistants IA", "Funciona con asistentes de IA", "עובד עם עוזרי AI")
add("No internet needed", "Sans connexion internet", "Sin necesidad de internet", "בלי צורך באינטרנט")
add("Illustration: a receipt is scanned on a phone, its details fill in and it's ready to submit",
    "Illustration : un reçu est photographié sur un téléphone, ses informations se remplissent et il est prêt à être remis",
    "Ilustración: se escanea un ticket en el móvil, sus datos se rellenan y queda listo para entregar",
    "איור: קבלה נסרקת בטלפון, הפרטים שלה מתמלאים והיא מוכנה להגשה")
add("Sep", "sept.", "sep", "ספט׳")
add("Oct", "oct.", "oct", "אוק׳")
add("November", "Novembre", "Noviembre", "נובמבר")
add("TOTAL FOR NOVEMBER", "TOTAL DE NOVEMBRE", "TOTAL DE NOVIEMBRE", "סה״כ לנובמבר")
add("VINE CAFÉ LTD", "CAFÉ DE LA VIGNE SARL", "CAFÉ LA VIÑA S.L.", "קפה הגפן בע״מ")
add("Reg. no. 514000000", "SIREN 514000000", "NIF 514000000", "ע.מ 514000000")
add("Salad", "Salade", "Ensalada", "סלט")
add("Coffee", "Café", "Café", "קפה")
add("VAT 18%", "TVA 18 %", "IVA 18 %", "מע״מ 18%")
add("TOTAL", "TOTAL", "TOTAL", "סה״כ")
add("Vendor", "Fournisseur", "Proveedor", "ספק")
add("Vine Café", "Café de la Vigne", "Café La Viña", "קפה הגפן")
add("Date", "Date", "Fecha", "תאריך")
add("VAT", "TVA", "IVA", "מע״מ")
add("Total", "Total", "Total", "סה״כ")
add("Ready to submit", "Prêt à remettre", "Listo para entregar", "מוכנה להגשה")
add("Approved", "Approuvé", "Aprobado", "אושר")
add("by Accounting", "par la comptabilité", "por contabilidad", "על ידי הנהלת החשבונות")
add("November exported", "Novembre exporté", "Noviembre exportado", "נובמבר יוצא")
add("Excel, with GL codes", "Excel, avec les comptes", "Excel, con códigos contables", "Excel, עם קודי חשבון")

# Mission
add("Why we built it", "Pourquoi nous l'avons créé", "Por qué lo creamos", "למה בנינו את זה")
add("From paper to done", "Fini la paperasse", "Adiós al papeleo", "סוף לניירת")
add("Refund-Me came to end manual documenting and submitting of expenses, and to bring them into a new, digital era that makes each person and the whole office more efficient.",
    "Refund-Me est né pour en finir avec la saisie et la remise manuelles des notes de frais, et les faire entrer dans une nouvelle ère numérique qui rend chacun, et tout le bureau, plus efficace.",
    "Refund-Me nació para acabar con el registro y la entrega manual de gastos, y llevarlos a una nueva era digital que hace más eficiente a cada persona y a toda la oficina.",
    "Refund-Me נועד לשים סוף לתיעוד ולהגשה ידניים של הוצאות, ולהביא אותם לעידן דיגיטלי חדש שמשפר את היעילות של כל אחד ושל המשרד כולו.")
add("Before", "Avant", "Antes", "לפני")
add("Expenses due Friday!", "Notes de frais pour vendredi !", "¡Gastos para el viernes!", "הוצאות עד שישי!")
add("Paper receipts kept in wallets and envelopes", "Des reçus papier gardés dans des portefeuilles et des enveloppes", "Tickets de papel guardados en carteras y sobres", "קבלות נייר בארנקים ובמעטפות")
add("Details typed into spreadsheets, forms printed and signed", "Des informations saisies dans des tableurs, des formulaires imprimés et signés", "Datos tecleados en hojas de cálculo, formularios impresos y firmados", "פרטים מוקלדים בגיליונות, טפסים מודפסים וחתומים")
add("Chased by email at month end, then re-typed by accounting", "Des relances par e-mail en fin de mois, puis une nouvelle saisie par la comptabilité", "Recordatorios por email a fin de mes y vuelta a teclear en contabilidad", "רדיפה במייל בסוף החודש, ואז הקלדה מחדש בהנהלת החשבונות")
add("With Refund-Me", "Avec Refund-Me", "Con Refund-Me", "עם Refund-Me")
add("Snap the receipt", "Photographiez le reçu", "Fotografía el ticket", "מצלמים את הקבלה")
add("phone camera", "appareil photo", "cámara del móvil", "מצלמת הטלפון")
add("The app reads it", "L'application le lit", "La app lo lee", "האפליקציה קוראת אותה")
add("details filled in", "informations remplies", "datos rellenados", "הפרטים מתמלאים")
add("Approved", "Approuvé", "Aprobado", "אישור")
add("manager, accounting", "manager, comptabilité", "responsable, contabilidad", "מנהל, הנהלת חשבונות")
add("The month goes to accounting", "Le mois part en comptabilité", "El mes llega a contabilidad", "החודש עובר להנהלת החשבונות")
add("One digital flow from the counter to the books", "Un seul parcours numérique, du comptoir à la comptabilité", "Un único flujo digital, del mostrador a la contabilidad", "תהליך דיגיטלי אחד, מהקופה ועד הספרים")
add("Checked, no flags", "Vérifié, sans alerte", "Revisado, sin avisos", "נבדק, בלי סימונים")
add("No paper, no re-typing", "Ni papier, ni ressaisie", "Sin papel, sin volver a teclear", "בלי נייר, בלי הקלדה מחדש")
add("The problem", "Le problème", "El problema", "הבעיה")
add("Expenses are still done by hand", "Les notes de frais se font encore à la main", "Los gastos se siguen haciendo a mano", "הוצאות עדיין מטופלות ביד")
add("Receipts on paper, details in spreadsheets, signatures, reminders and re-typing: hours of work that adds nothing.",
    "Des reçus papier, des tableurs, des signatures, des relances et des ressaisies : des heures de travail qui n'apportent rien.",
    "Tickets en papel, hojas de cálculo, firmas, recordatorios y volver a teclear: horas de trabajo que no aportan nada.",
    "קבלות נייר, פרטים בגיליונות, חתימות, תזכורות והקלדה מחדש: שעות של עבודה שלא מוסיפות כלום.")
add("For each person", "Pour chacun", "Para cada persona", "לכל אחד")
add("A minute per receipt", "Une minute par reçu", "Un minuto por ticket", "דקה לקבלה")
add("Snap it when you pay instead of spending an evening at month end. Nothing gets lost.",
    "Photographiez-le en payant au lieu d'y passer une soirée en fin de mois. Rien ne se perd.",
    "Fotografíalo al pagar en lugar de pasar una tarde a fin de mes. No se pierde nada.",
    "מצלמים בזמן התשלום במקום לבזבז ערב בסוף החודש. שום דבר לא הולך לאיבוד.")
add("For the office", "Pour le bureau", "Para la oficina", "למשרד")
add("A faster, cleaner close", "Une clôture plus rapide et plus propre", "Un cierre más rápido y limpio", "סגירת חודש מהירה ונקייה")
add("Managers approve in a tap; accounting closes the month faster, with fewer errors and a full audit trail.",
    "Les managers approuvent d'un geste ; la comptabilité clôture le mois plus vite, avec moins d'erreurs et une traçabilité complète.",
    "Los responsables aprueban con un toque; contabilidad cierra el mes más rápido, con menos errores y un registro completo.",
    "המנהלים מאשרים בנגיעה; הנהלת החשבונות סוגרת את החודש מהר יותר, עם פחות טעויות ותיעוד מלא.")

# Facts
add("4 steps", "4 étapes", "4 pasos", "4 שלבים")
add("Snap, check, approve, export", "Photographier, vérifier, approuver, exporter", "Fotografiar, revisar, aprobar, exportar", "מצלמים, בודקים, מאשרים, מייצאים")
add("4 languages", "4 langues", "4 idiomas", "4 שפות")
add("Hebrew, English, French and Spanish", "Hébreu, anglais, français et espagnol", "Hebreo, inglés, francés y español", "עברית, אנגלית, צרפתית וספרדית")
add("4 databases", "4 bases de données", "4 bases de datos", "4 מסדי נתונים")
add("Built-in, PostgreSQL, SQL Server, MySQL", "Intégrée, PostgreSQL, SQL Server, MySQL", "Integrada, PostgreSQL, SQL Server, MySQL", "מובנה, PostgreSQL, SQL Server, MySQL")
add("0 bytes", "0 octet", "0 bytes", "0 בייטים")
add("leave your server unless you turn on cloud AI", "ne quittent votre serveur, sauf si vous activez l'IA cloud", "salen de tu servidor salvo que actives la IA en la nube", "יוצאים מהשרת, אלא אם מפעילים AI בענן")

# Why
add("Why Refund-Me", "Pourquoi Refund-Me", "Por qué Refund-Me", "למה Refund-Me")
add("Month end without the paper chase", "Une fin de mois sans chasse aux papiers", "Fin de mes sin perseguir papeles", "סוף חודש בלי לרדוף אחרי ניירת")
add("Everything that makes expenses slow and error-prone, handled for you.", "Tout ce qui rend les notes de frais lentes et sources d'erreurs, pris en charge pour vous.", "Todo lo que hace los gastos lentos y propensos a errores, resuelto por ti.", "כל מה שהופך הוצאות לאיטיות ומועדות לטעויות, מטופל בשבילכם.")
add("Receipts lost in wallets and car seats", "Des reçus perdus dans les portefeuilles et sous les sièges", "Tickets perdidos en carteras y asientos del coche", "קבלות שאובדות בארנק ובמושב הרכב")
add("A photo the moment you pay. The app keeps it.", "Une photo au moment de payer. L'application la garde.", "Una foto en el momento de pagar. La app la guarda.", "תמונה ברגע התשלום. האפליקציה שומרת אותה.")
add("Typing amounts, dates and VAT numbers into Excel", "Saisir montants, dates et numéros de TVA dans Excel", "Teclear importes, fechas y números de IVA en Excel", "הקלדת סכומים, תאריכים ומספרי עוסק לאקסל")
add("The app reads the business, ID, date, total, VAT and receipt number", "L'application lit l'entreprise, son numéro, la date, le total, la TVA et le numéro du reçu", "La app lee el comercio, su número, la fecha, el total, el IVA y el número del ticket", "האפליקציה קוראת את העסק, המספר שלו, התאריך, הסכום, המע״מ ומספר הקבלה")
add("“Did you get my expenses?” emails", "Les e-mails « Tu as reçu mes notes de frais ? »", "Emails de «¿Te llegaron mis gastos?»", "מיילים של “קיבלת את ההוצאות שלי?”")
add("Everyone sees where their month stands", "Chacun voit où en est son mois", "Cada uno ve en qué punto está su mes", "כל אחד רואה איפה החודש שלו עומד")
add("Chasing people at the end of the month", "Relancer tout le monde en fin de mois", "Perseguir a la gente a fin de mes", "רדיפה אחרי אנשים בסוף החודש")
add("Automatic reminders before the due day, one click to remind everyone", "Des rappels automatiques avant l'échéance, un clic pour relancer tout le monde", "Recordatorios automáticos antes del plazo, un clic para avisar a todos", "תזכורות אוטומטיות לפני מועד ההגשה, ולחיצה אחת כדי להזכיר לכולם")
add("Checking every receipt by eye", "Vérifier chaque reçu à l'œil", "Revisar cada ticket a ojo", "בדיקה של כל קבלה בעין")
add("Flags for possible duplicates, over-the-limit amounts and missing details", "Des alertes pour les doublons possibles, les dépassements de plafond et les informations manquantes", "Avisos de posibles duplicados, importes por encima del límite y datos que faltan", "סימונים לכפילויות אפשריות, חריגות מתקרה ופרטים חסרים")
add("Re-typing it all into the accounting system", "Tout ressaisir dans le logiciel comptable", "Volver a teclearlo todo en el sistema contable", "הקלדה מחדש של הכול למערכת הנהלת החשבונות")
add("Converting receipts from trips abroad by hand", "Convertir à la main les reçus des déplacements à l'étranger", "Convertir a mano los tickets de los viajes al extranjero", "המרה ידנית של קבלות מנסיעות לחו\"ל")
add("Receipts in any currency, converted at the day's official rate", "Des reçus dans toutes les devises, convertis au taux officiel du jour", "Tickets en cualquier moneda, convertidos al tipo oficial del día", "קבלות בכל מטבע, מומרות לפי השער היציג של היום")
add("Export the month with account (GL) codes, ready to import", "Exportez le mois avec les numéros de compte, prêt à importer", "Exporta el mes con los códigos contables, listo para importar", "ייצוא החודש עם קודי חשבון, מוכן לקליטה")

# How it works
add("From the café counter to the accounting system", "Du comptoir du café au logiciel comptable", "Del mostrador de la cafetería al sistema contable", "מהקופה בבית הקפה ועד מערכת הנהלת החשבונות")
add("Snap", "Photographier", "Fotografiar", "מצלמים")
add("Scan receipts one after another with the phone camera, or upload photos and PDFs.", "Photographiez les reçus les uns après les autres avec l'appareil photo, ou importez des photos et des PDF.", "Escanea tickets uno tras otro con la cámara del móvil, o sube fotos y PDF.", "סורקים קבלות אחת אחרי השנייה במצלמת הטלפון, או מעלים תמונות וקובצי PDF.")
add("Check", "Vérifier", "Revisar", "בודקים")
add("The details fill themselves in. Fix anything misread, then hand in the month.", "Les informations se remplissent toutes seules. Corrigez ce qui a été mal lu, puis remettez le mois.", "Los datos se rellenan solos. Corrige lo que se haya leído mal y entrega el mes.", "הפרטים מתמלאים לבד. מתקנים מה שנקרא לא נכון, ומגישים את החודש.")
add("Approve", "Approuver", "Aprobar", "מאשרים")
add("The manager (if you want that step), then accounting. Anything wrong goes back with a note.", "Le manager (si vous le souhaitez), puis la comptabilité. Ce qui ne va pas revient avec une note.", "El responsable (si quieres ese paso) y luego contabilidad. Lo que esté mal vuelve con una nota.", "המנהל (אם רוצים את השלב הזה), ואז הנהלת החשבונות. מה שלא תקין חוזר עם הערה.")
add("Export", "Exporter", "Exportar", "מייצאים")
add("Close the month: Excel or CSV for accounting, and a branded PDF per employee, with photos.", "Clôturez le mois : Excel ou CSV pour la comptabilité, et un PDF à vos couleurs par employé, avec les photos.", "Cierra el mes: Excel o CSV para contabilidad y un PDF con tu marca por empleado, con fotos.", "סוגרים את החודש: Excel או CSV להנהלת החשבונות, ודוח PDF ממותג לכל עובד, עם התמונות.")
add("Illustration: a receipt travels from the employee to the manager, to accounting, to the export", "Illustration : un reçu passe de l'employé au manager, puis à la comptabilité et à l'export", "Ilustración: un ticket pasa del empleado al responsable, a contabilidad y a la exportación", "איור: קבלה עוברת מהעובד למנהל, להנהלת החשבונות ולייצוא")
add("Employee", "Employé", "Empleado", "עובד")
add("hands in the month", "remet le mois", "entrega el mes", "מגיש את החודש")
add("Manager", "Manager", "Responsable", "מנהל")
add("approves the team", "approuve l'équipe", "aprueba al equipo", "מאשר את הצוות")
add("Accounting", "Comptabilité", "Contabilidad", "הנהלת חשבונות")
add("approves and closes", "approuve et clôture", "aprueba y cierra", "מאשרת וסוגרת")
add("to the accounting system", "vers le logiciel comptable", "al sistema contable", "למערכת הנהלת החשבונות")

# Roles
add("Something for everyone", "Pour chacun", "Algo para cada uno", "משהו לכל אחד")
add("Each person sees what they need, and only that", "Chacun voit ce dont il a besoin, et seulement cela", "Cada persona ve lo que necesita, y solo eso", "כל אחד רואה מה שהוא צריך, ורק את זה")
add("Employees", "Employés", "Empleados", "עובדים")
add("Scan many receipts in a row", "Photographiez plusieurs reçus à la suite", "Escanea muchos tickets seguidos", "סריקה של הרבה קבלות ברצף")
add("Photos, PDFs and iPhone HEIC", "Photos, PDF et HEIC d'iPhone", "Fotos, PDF y HEIC de iPhone", "תמונות, PDF ו-HEIC מאייפון")
add("The month at a glance: ready, needs you, handed in", "Le mois d'un coup d'œil : prêt, à compléter, remis", "El mes de un vistazo: listo, te necesita, entregado", "החודש במבט אחד: מוכן, דורש טיפול, הוגש")
add("Returned receipts say what to fix", "Les reçus renvoyés disent quoi corriger", "Los tickets devueltos dicen qué corregir", "קבלות שהוחזרו אומרות מה לתקן")
add("Your own Insights", "Vos propres statistiques", "Tus propias estadísticas", "תובנות משלכם")
add("Managers", "Managers", "Responsables", "מנהלים")
add("One email per employee and month", "Un e-mail par employé et par mois", "Un email por empleado y mes", "מייל אחד לכל עובד וחודש")
add("Approve a month or single receipts", "Approuvez un mois ou des reçus un par un", "Aprueba un mes o tickets sueltos", "אישור חודש שלם או קבלות בודדות")
add("Return with a note", "Renvoyez avec une note", "Devuelve con una nota", "החזרה עם הערה")
add("Team Insights", "Statistiques de l'équipe", "Estadísticas del equipo", "תובנות הצוות")
add("Everyone's months on one page, with flags", "Les mois de tous sur une page, avec les alertes", "Los meses de todos en una página, con avisos", "החודשים של כולם בעמוד אחד, עם סימונים")
add("Approve one, several or a month", "Approuvez un, plusieurs ou un mois entier", "Aprueba uno, varios o un mes", "אישור אחת, כמה או חודש שלם")
add("Close, reopen, export", "Clôturer, rouvrir, exporter", "Cerrar, reabrir, exportar", "סגירה, פתיחה מחדש, ייצוא")
add("Expense types with GL codes and monthly limits", "Types de dépenses avec comptes et plafonds mensuels", "Tipos de gasto con códigos contables y límites mensuales", "סוגי הוצאות עם קודי חשבון ותקרות חודשיות")
add("Remind everyone in one click", "Relancez tout le monde en un clic", "Avisa a todos con un clic", "תזכורת לכולם בלחיצה")
add("Admins", "Administrateurs", "Administradores", "מנהלי מערכת")
add("Your name, logo and colors everywhere", "Votre nom, votre logo et vos couleurs partout", "Tu nombre, logotipo y colores en todas partes", "השם, הלוגו והצבעים שלכם בכל מקום")
add("Microsoft, Google, email-link or password sign-in", "Connexion par Microsoft, Google, lien par e-mail ou mot de passe", "Acceso con Microsoft, Google, enlace por email o contraseña", "כניסה עם Microsoft, Google, קישור במייל או סיסמה")
add("Activity log, alerts, backups", "Journal d'activité, alertes, sauvegardes", "Registro de actividad, alertas, copias de seguridad", "יומן פעילות, התראות, גיבויים")
add("AI assistants on or off, per role", "Assistants IA activés ou non, par rôle", "Asistentes de IA activados o no, por rol", "עוזרי AI מופעלים או כבויים, לפי תפקיד")

# Devices
add("Works on every device", "Sur tous les appareils", "En todos los dispositivos", "עובד בכל מכשיר")
add("Phone first. Just as good on a big screen.", "Pensé pour le téléphone. Tout aussi bien sur grand écran.", "Primero el móvil. Igual de bien en pantalla grande.", "קודם כול טלפון. טוב באותה מידה במסך גדול.")
add("One app that fits the screen it's on: a thumb-friendly phone, a roomy tablet, a side-by-side desk view.", "Une seule application qui s'adapte à l'écran : un téléphone pensé pour le pouce, une tablette spacieuse, une vue côte à côte au bureau.", "Una sola app que se adapta a la pantalla: un móvil cómodo para el pulgar, una tableta amplia y una vista lado a lado en el escritorio.", "אפליקציה אחת שמתאימה את עצמה למסך: טלפון נוח לאגודל, טאבלט מרווח, ותצוגה זה לצד זה במחשב.")
add("Computer: list and receipt side by side", "Ordinateur : liste et reçu côte à côte", "Ordenador: lista y ticket lado a lado", "מחשב: הרשימה והקבלה זו לצד זו")
add("Tablet", "Tablette", "Tableta", "טאבלט")
add("Phone: menu at the bottom", "Téléphone : menu en bas", "Móvil: menú abajo", "טלפון: תפריט בתחתית")
add("Install it like an app", "Installez-la comme une application", "Instálala como una app", "התקנה כמו אפליקציה")
add("Add it to the home screen on iPhone, iPad or Android: full screen, its own icon, no app store. The app's install page shows how, step by step.", "Ajoutez-la à l'écran d'accueil sur iPhone, iPad ou Android : plein écran, sa propre icône, sans magasin d'applications. La page d'installation de l'application montre comment, étape par étape.", "Añádela a la pantalla de inicio en iPhone, iPad o Android: pantalla completa, su propio icono, sin tienda de apps. La página de instalación de la app muestra cómo, paso a paso.", "מוסיפים אותה למסך הבית באייפון, באייפד או באנדרואיד: מסך מלא, סמל משלה, בלי חנות אפליקציות. דף ההתקנה של האפליקציה מראה איך, שלב אחרי שלב.")
add("Made for thumbs and mice", "Faite pour le pouce et la souris", "Hecha para el pulgar y el ratón", "מותאמת לאגודל ולעכבר")
add("Big buttons and the camera one tap away on the phone. Press and hold a receipt for the same menu a right-click opens on a computer. Headers and filters stay in view as you scroll.", "De grands boutons et l'appareil photo à portée de doigt sur le téléphone. Un appui long sur un reçu ouvre le même menu qu'un clic droit sur ordinateur. Les en-têtes et les filtres restent visibles quand on fait défiler.", "Botones grandes y la cámara a un toque en el móvil. Mantén pulsado un ticket para abrir el mismo menú que el clic derecho en el ordenador. Los encabezados y filtros siguen a la vista al desplazarte.", "כפתורים גדולים והמצלמה במרחק נגיעה בטלפון. לחיצה ארוכה על קבלה פותחת את אותו תפריט שלחיצה ימנית פותחת במחשב. הכותרות והמסננים נשארים גלויים בזמן הגלילה.")
add("Four languages, your colors", "Quatre langues, vos couleurs", "Cuatro idiomas, tus colores", "ארבע שפות, הצבעים שלכם")
add("Each person in their own language with real right-to-left screens. Light, dark, navy or warm, the same on every device. Your logo on screens and reports.", "Chacun dans sa langue, avec de vrais écrans de droite à gauche. Clair, sombre, marine ou chaud, le même sur chaque appareil. Votre logo sur les écrans et les rapports.", "Cada persona en su idioma, con pantallas de derecha a izquierda de verdad. Claro, oscuro, marino o cálido, igual en todos los dispositivos. Tu logotipo en pantallas e informes.", "כל אחד בשפה שלו, עם מסכי ימין-לשמאל אמיתיים. בהיר, כהה, כחול או חם, אותו דבר בכל מכשיר. הלוגו שלכם על המסכים ובדוחות.")

# AI assistants
add("Ask your AI assistant", "Demandez à votre assistant IA", "Pregunta a tu asistente de IA", "שואלים את עוזר ה-AI")
add("Your expenses, one question away", "Vos notes de frais, à une question près", "Tus gastos, a una pregunta de distancia", "ההוצאות שלכם, במרחק שאלה אחת")
add("Connect Claude, Cursor, VS Code or any assistant that speaks MCP, and ask in plain words. It works as you, with your permissions, and nothing changes without your OK.", "Connectez Claude, Cursor, VS Code ou tout assistant compatible MCP, et demandez simplement. Il agit en votre nom, avec vos droits, et rien ne change sans votre accord.", "Conecta Claude, Cursor, VS Code o cualquier asistente compatible con MCP y pregunta con tus palabras. Actúa como tú, con tus permisos, y nada cambia sin tu visto bueno.", "מחברים את Claude,‏ Cursor,‏ VS Code או כל עוזר שתומך ב-MCP, ושואלים במילים פשוטות. הוא פועל בשמכם, עם ההרשאות שלכם, ושום דבר לא משתנה בלי אישור שלכם.")
add("“What's still missing in my June?” · “Submit my month.”", "« Que manque-t-il encore pour juin ? » · « Remets mon mois. »", "«¿Qué me falta todavía en junio?» · «Entrega mi mes.»", "“מה עוד חסר לי ביוני?” · “תגיש את החודש שלי.”")
add("“What's waiting for my approval?”", "« Qu'est-ce qui attend mon approbation ? »", "«¿Qué está pendiente de mi aprobación?»", "“מה מחכה לאישור שלי?”")
add("“How much did Sales spend on fuel this year?” · “Export November to Excel.”", "« Combien les ventes ont-elles dépensé en carburant cette année ? » · « Exporte novembre vers Excel. »", "«¿Cuánto gastó Ventas en combustible este año?» · «Exporta noviembre a Excel.»", "“כמה הוציאו במכירות על דלק השנה?” · “תייצא את נובמבר לאקסל.”")
add("Admin", "Administrateur", "Administrador", "מנהל מערכת")
add("“Who changed the settings this week?”", "« Qui a modifié les réglages cette semaine ? »", "«¿Quién cambió la configuración esta semana?»", "“מי שינה את ההגדרות השבוע?”")
add("You, not more", "Vous, pas plus", "Tú, no más", "אתם, לא יותר")
add("A personal token with exactly your permissions.", "Un jeton personnel avec exactement vos droits.", "Un token personal con exactamente tus permisos.", "טוקן אישי עם בדיוק ההרשאות שלכם.")
add("Preview, then confirm", "Aperçu, puis confirmation", "Vista previa, luego confirmación", "תצוגה מקדימה, ואז אישור")
add("Submitting, approving and closing always ask first.", "Remettre, approuver et clôturer demandent toujours d'abord.", "Entregar, aprobar y cerrar siempre preguntan antes.", "הגשה, אישור וסגירה תמיד שואלים קודם.")
add("Your limits", "Vos limites", "Tus límites", "הגבולות שלכם")
add("Read-only tokens, expiry dates, revoke one or all.", "Jetons en lecture seule, dates d'expiration, révocation d'un ou de tous.", "Tokens de solo lectura, fechas de caducidad, revoca uno o todos.", "טוקנים לקריאה בלבד, תאריכי תפוגה, ביטול של אחד או של כולם.")
add("Off until you say", "Désactivé tant que vous ne dites rien", "Apagado hasta que lo digas", "כבוי עד שתחליטו")
add("Admins choose who may connect and whether photos are shared.", "Les administrateurs choisissent qui peut se connecter et si les photos sont partagées.", "Los administradores eligen quién puede conectarse y si se comparten las fotos.", "מנהלי המערכת בוחרים מי יכול להתחבר והאם התמונות משותפות.")
add("Illustration: a manager asks an assistant what's waiting, sees a preview and approves", "Illustration : un manager demande à un assistant ce qui attend, voit un aperçu et approuve", "Ilustración: un responsable pregunta a un asistente qué está pendiente, ve una vista previa y aprueba", "איור: מנהל שואל עוזר מה מחכה, רואה תצוגה מקדימה ומאשר")
add("Assistant · connected to Refund-Me", "Assistant · connecté à Refund-Me", "Asistente · conectado a Refund-Me", "עוזר · מחובר ל-Refund-Me")
add("What's waiting for my approval?", "Qu'est-ce qui attend mon approbation ?", "¿Qué está pendiente de mi aprobación?", "מה מחכה לאישור שלי?")
add("Two months:", "Deux mois :", "Dos meses:", "שני חודשים:")
add("Dana Levi", "Claire Martin", "Lucía García", "דנה לוי")
add(", October, 6 receipts,", ", octobre, 6 reçus,", ", octubre, 6 tickets,", ", אוקטובר, 6 קבלות,")
add(", one flagged as a possible duplicate;", ", dont un signalé comme doublon possible ;", ", uno marcado como posible duplicado;", ", אחת מסומנת ככפילות אפשרית;")
add("Omer Katz", "Hugo Bernard", "Pablo Ruiz", "עומר כץ")
add(", October, 3 receipts,", ", octobre, 3 reçus,", ", octubre, 3 tickets,", ", אוקטובר, 3 קבלות,")
add(". Want to see Dana's flagged receipt?", ". Voulez-vous voir le reçu signalé de Claire ?", ". ¿Quieres ver el ticket marcado de Lucía?", ". רוצה לראות את הקבלה המסומנת של דנה?")
add("Yes, I checked it. Approve Omer's month.", "Oui, je l'ai vérifié. Approuve le mois d'Hugo.", "Sí, ya lo revisé. Aprueba el mes de Pablo.", "כן, בדקתי אותה. תאשר את החודש של עומר.")
add("Preview: 3 receipts,", "Aperçu : 3 reçus,", "Vista previa: 3 tickets,", "תצוגה מקדימה: 3 קבלות,")
add(", nothing flagged. Approve?", ", rien de signalé. Approuver ?", ", nada marcado. ¿Aprobar?", ", אין סימונים. לאשר?")
add("✓ Confirmed: approved and sent on to accounting.", "✓ Confirmé : approuvé et transmis à la comptabilité.", "✓ Confirmado: aprobado y enviado a contabilidad.", "✓ אושר והועבר להנהלת החשבונות.")

# Data
add("Your data stays yours", "Vos données restent les vôtres", "Tus datos siguen siendo tuyos", "המידע שלכם נשאר שלכם")
add("Installed on your server. Owned by you.", "Installé sur votre serveur. À vous.", "Instalado en tu servidor. Tuyo.", "מותקן על השרת שלכם. בבעלותכם.")
add("One install per company", "Une installation par entreprise", "Una instalación por empresa", "התקנה אחת לכל חברה")
add("On your server or cloud account. You own the database and the files.", "Sur votre serveur ou votre compte cloud. La base de données et les fichiers sont à vous.", "En tu servidor o tu cuenta en la nube. La base de datos y los archivos son tuyos.", "על השרת או חשבון הענן שלכם. מסד הנתונים והקבצים שלכם.")
add("Receipts are read and PDF reports are made on the server itself. The only thing it fetches is the day's exchange rates, which can be entered by hand instead.", "Les reçus sont lus et les rapports PDF sont produits sur le serveur lui-même. Il ne récupère que les taux de change du jour, qui peuvent aussi être saisis à la main.", "Los tickets se leen y los informes PDF se generan en el propio servidor. Lo único que obtiene son los tipos de cambio del día, que también se pueden introducir a mano.", "הקבלות נקראות ודוחות ה-PDF נוצרים על השרת עצמו. הדבר היחיד שהוא מושך הוא שערי החליפין של היום, ואפשר גם להזין אותם ידנית.")
add("Cloud AI only if you choose", "L'IA cloud seulement si vous le choisissez", "IA en la nube solo si tú quieres", "AI בענן רק אם בוחרים")
add("Connect Anthropic, OpenAI, xAI, OpenRouter or your own GPU server for even better reading. Off until an admin turns it on and confirms.", "Connectez Anthropic, OpenAI, xAI, OpenRouter ou votre propre serveur GPU pour une lecture encore meilleure. Désactivé tant qu'un administrateur ne l'active pas et ne confirme pas.", "Conecta Anthropic, OpenAI, xAI, OpenRouter o tu propio servidor GPU para una lectura aún mejor. Apagado hasta que un administrador lo active y lo confirme.", "מחברים את Anthropic,‏ OpenAI,‏ xAI,‏ OpenRouter או שרת GPU משלכם לקריאה טובה עוד יותר. כבוי עד שמנהל מערכת מפעיל ומאשר.")
add("Less kept, less at risk", "Moins conservé, moins exposé", "Menos guardado, menos riesgo", "פחות נשמר, פחות בסיכון")
add("The raw text read from receipts is deleted after 30 days.", "Le texte brut lu sur les reçus est supprimé après 30 jours.", "El texto en bruto leído de los tickets se borra a los 30 días.", "הטקסט הגולמי שנקרא מהקבלות נמחק אחרי 30 יום.")
add("Illustration: the app, database and receipt files inside your server; cloud AI switched off", "Illustration : l'application, la base de données et les fichiers de reçus dans votre serveur ; l'IA cloud désactivée", "Ilustración: la app, la base de datos y los archivos de tickets dentro de tu servidor; la IA en la nube apagada", "איור: האפליקציה, מסד הנתונים וקובצי הקבלות בתוך השרת שלכם; AI בענן כבוי")
add("the app", "l'application", "la app", "האפליקציה")
add("Receipt reading", "Lecture des reçus", "Lectura de tickets", "קריאת קבלות")
add("built in", "intégrée", "integrada", "מובנית")
add("Database", "Base de données", "Base de datos", "מסד נתונים")
add("yours", "à vous", "tuya", "שלכם")
add("Receipt photos", "Photos des reçus", "Fotos de tickets", "תמונות קבלות")
add("Cloud AI: off by default", "IA cloud : désactivée par défaut", "IA en la nube: apagada por defecto", "AI בענן: כבוי כברירת מחדל")

# SSO
add("Single sign-on (SSO)", "Authentification unique (SSO)", "Inicio de sesión único (SSO)", "כניסה אחודה (SSO)")
add("Sign in with the work account you already have", "Connectez-vous avec le compte professionnel que vous avez déjà", "Entra con la cuenta de trabajo que ya tienes", "נכנסים עם חשבון העבודה שכבר יש לכם")
add("Connect Microsoft Entra ID (Microsoft 365) or Google Workspace, and your people sign in with one click. No new password to remember, and nothing new for IT to manage.", "Connectez Microsoft Entra ID (Microsoft 365) ou Google Workspace, et vos équipes se connectent en un clic. Aucun nouveau mot de passe à retenir, rien de nouveau à gérer pour l'informatique.", "Conecta Microsoft Entra ID (Microsoft 365) o Google Workspace y tu gente entra con un clic. Ninguna contraseña nueva que recordar y nada nuevo que gestionar para TI.", "מחברים את Microsoft Entra ID ‏(Microsoft 365) או Google Workspace, והעובדים נכנסים בלחיצה. אין סיסמה חדשה לזכור, ואין משהו חדש לנהל ב-IT.")
add("Your sign-in rules apply", "Vos règles de connexion s'appliquent", "Se aplican tus reglas de acceso", "כללי הכניסה שלכם חלים")
add("People sign in at Microsoft or Google, so your company's own rules, such as two-step verification, cover Refund-Me too.", "La connexion se fait chez Microsoft ou Google : les règles de votre entreprise, comme la vérification en deux étapes, couvrent aussi Refund-Me.", "El acceso se hace en Microsoft o Google, así que las reglas de tu empresa, como la verificación en dos pasos, también cubren Refund-Me.", "הכניסה נעשית ב-Microsoft או ב-Google, ולכן הכללים של החברה שלכם, כמו אימות דו-שלבי, חלים גם על Refund-Me.")
add("Only your organization", "Seulement votre organisation", "Solo tu organización", "רק הארגון שלכם")
add('Microsoft sign-in is tied to your own tenant, never "any Microsoft account", and only people on the list get in. A colleague who isn\'t on it yet waits for an admin or accountant to approve them.',
    "La connexion Microsoft est liée à votre propre tenant, jamais à « n'importe quel compte Microsoft », et seules les personnes de la liste entrent. Un collègue qui n'y figure pas encore attend qu'un administrateur ou un comptable l'approuve.",
    "El acceso con Microsoft está ligado a tu propio tenant, nunca a «cualquier cuenta de Microsoft», y solo entra quien está en la lista. Un compañero que aún no está espera a que un administrador o contable lo apruebe.",
    "הכניסה עם Microsoft קשורה ל-tenant שלכם, אף פעם לא ל“כל חשבון Microsoft”, ורק מי שברשימה נכנס. עמית שעוד לא ברשימה מחכה שמנהל מערכת או מנהלת חשבונות יאשרו אותו.")
add("Leavers are out", "Les départs sont exclus", "Quien se va, queda fuera", "מי שעוזב, בחוץ")
add("Disable someone's work account and they can no longer sign in with it; turn them off in Refund-Me and they're signed out everywhere at once.", "Désactivez le compte professionnel d'une personne et elle ne peut plus s'en servir pour se connecter ; désactivez-la dans Refund-Me et elle est déconnectée partout à la fois.", "Desactiva la cuenta de trabajo de alguien y ya no podrá entrar con ella; desactívalo en Refund-Me y se cierra su sesión en todas partes a la vez.", "משביתים חשבון עבודה של מישהו והוא כבר לא יכול להיכנס איתו; מכבים אותו ב-Refund-Me והוא מנותק מכל המכשירים בבת אחת.")
add("No lock-outs", "Jamais bloqué dehors", "Sin quedarse fuera", "בלי נעילה בחוץ")
add("One-time email links and passwords are there for those who need them, and can be switched off once SSO works. Admins can always sign in, so a broken SSO setup can't lock everyone out.", "Les liens à usage unique par e-mail et les mots de passe restent là pour ceux qui en ont besoin, et peuvent être désactivés une fois le SSO en place. Les administrateurs peuvent toujours se connecter : un SSO mal configuré ne bloque pas tout le monde.", "Los enlaces de un solo uso por email y las contraseñas siguen ahí para quien los necesite, y se pueden desactivar cuando el SSO funcione. Los administradores siempre pueden entrar, así que un SSO mal configurado no deja a todos fuera.", "קישורים חד-פעמיים במייל וסיסמאות זמינים למי שצריך, ואפשר לכבות אותם כשה-SSO עובד. מנהלי מערכת תמיד יכולים להיכנס, כך שהגדרת SSO שבורה לא נועלת את כולם בחוץ.")
add("Set up in the wizard", "Configuré dans l'assistant", "Se configura en el asistente", "מוגדר באשף")
add("Paste the app ID and secret from your Microsoft or Google admin console; the guide shows exactly where.", "Collez l'identifiant et le secret de l'application depuis votre console d'administration Microsoft ou Google ; le guide montre exactement où.", "Pega el ID y el secreto de la aplicación desde tu consola de administración de Microsoft o Google; la guía muestra exactamente dónde.", "מדביקים את מזהה האפליקציה והסוד ממסוף הניהול של Microsoft או Google; המדריך מראה בדיוק איפה.")
add("Illustration: the sign-in page with Microsoft, Google and email-link sign-in", "Illustration : la page de connexion avec Microsoft, Google et le lien par e-mail", "Ilustración: la página de acceso con Microsoft, Google y enlace por email", "איור: דף הכניסה עם Microsoft,‏ Google וקישור במייל")
add("Sign in to Acme expenses", "Connexion aux notes de frais Acme", "Entrar en gastos de Acme", "כניסה להוצאות אקמה")
add("Use your work account.", "Utilisez votre compte professionnel.", "Usa tu cuenta de trabajo.", "השתמשו בחשבון העבודה.")
add("Continue with Microsoft", "Continuer avec Microsoft", "Continuar con Microsoft", "המשך עם Microsoft")
add("Continue with Google", "Continuer avec Google", "Continuar con Google", "המשך עם Google")
add("or", "ou", "o", "או")
add("noa@acme.example", "lea@acme.example", "carmen@acme.example", "noa@acme.example")
add("Email me a link", "M'envoyer un lien", "Envíame un enlace", "שלחו לי קישור")

# Security
add("Security, in plain words", "La sécurité, en mots simples", "La seguridad, en palabras sencillas", "אבטחה, במילים פשוטות")
add("Money and personal details, protected", "L'argent et les données personnelles, protégés", "Dinero y datos personales, protegidos", "כסף ופרטים אישיים, מוגנים")
add("Receipts carry names, amounts, card digits and car plates. Here's what keeps them safe.", "Les reçus contiennent des noms, des montants, des chiffres de carte et des plaques d'immatriculation. Voici ce qui les protège.", "Los tickets llevan nombres, importes, dígitos de tarjeta y matrículas. Esto es lo que los protege.", "קבלות כוללות שמות, סכומים, ספרות של כרטיס ומספרי רכב. הנה מה ששומר עליהן.")
add("Only your people get in", "Seuls vos collaborateurs entrent", "Solo entra tu gente", "רק האנשים שלכם נכנסים")
add("Only people on the list can sign in, with Microsoft or Google work accounts, a one-time email link or a password. Password guessing is paused automatically.", "Seules les personnes de la liste peuvent se connecter, avec un compte professionnel Microsoft ou Google, un lien unique par e-mail ou un mot de passe. Les tentatives de deviner un mot de passe sont bloquées automatiquement.", "Solo la gente de la lista puede entrar, con cuentas de trabajo de Microsoft o Google, un enlace de un solo uso por email o una contraseña. Los intentos de adivinar contraseñas se frenan automáticamente.", "רק מי שברשימה יכול להיכנס, עם חשבון עבודה של Microsoft או Google, קישור חד-פעמי במייל או סיסמה. ניחוש סיסמאות נעצר אוטומטית.")
add("Proof for big changes", "Une preuve pour les grands changements", "Una prueba para los cambios importantes", "הוכחה לשינויים גדולים")
add("Making an admin, changing sign-in or email settings, resetting data or loading a backup needs a fresh sign-in or the password. A stolen open session isn't enough.", "Nommer un administrateur, modifier la connexion ou l'e-mail, réinitialiser les données ou charger une sauvegarde exige une connexion récente ou le mot de passe. Une session volée ne suffit pas.", "Nombrar un administrador, cambiar el acceso o el correo, restablecer los datos o cargar una copia exige un acceso reciente o la contraseña. Una sesión robada no basta.", "מינוי מנהל מערכת, שינוי הגדרות כניסה או מייל, איפוס נתונים או טעינת גיבוי דורשים כניסה טרייה או את הסיסמה. סשן גנוב לא מספיק.")
add("See only what's yours", "Ne voir que ce qui vous concerne", "Ver solo lo tuyo", "רואים רק את מה ששלכם")
add("Employees see their own expenses, managers their team, accounting the company. AI assistants get exactly their owner's permissions, and can be read-only.", "Les employés voient leurs propres notes, les managers leur équipe, la comptabilité l'entreprise. Les assistants IA ont exactement les droits de leur propriétaire, et peuvent être en lecture seule.", "Los empleados ven sus propios gastos, los responsables su equipo y contabilidad la empresa. Los asistentes de IA tienen exactamente los permisos de su dueño y pueden ser de solo lectura.", "עובדים רואים את ההוצאות שלהם, מנהלים את הצוות, הנהלת החשבונות את החברה. עוזרי AI מקבלים בדיוק את ההרשאות של הבעלים שלהם, ויכולים להיות לקריאה בלבד.")
add("Secrets stay secret", "Les secrets restent secrets", "Los secretos siguen siendo secretos", "סודות נשארים סודיים")
add("Saved passwords and keys are encrypted, and the key can live apart from the data. The app's own database login can only read and write its data.", "Les mots de passe et clés enregistrés sont chiffrés, et la clé peut être conservée à part des données. Le compte de base de données de l'application ne peut que lire et écrire ses données.", "Las contraseñas y claves guardadas se cifran, y la clave puede guardarse aparte de los datos. El usuario de base de datos de la app solo puede leer y escribir sus datos.", "סיסמאות ומפתחות שנשמרים מוצפנים, והמפתח יכול להישמר בנפרד מהנתונים. משתמש מסד הנתונים של האפליקציה יכול רק לקרוא ולכתוב את הנתונים שלה.")
add("Nothing happens quietly", "Rien ne se passe en silence", "Nada pasa en silencio", "שום דבר לא קורה בשקט")
add("An activity log of who did what, when and from where, which nobody can edit or delete. Other admins are alerted to settings and admin changes.", "Un journal d'activité de qui a fait quoi, quand et d'où, que personne ne peut modifier ni supprimer. Les autres administrateurs sont alertés des changements de réglages et d'administrateurs.", "Un registro de actividad de quién hizo qué, cuándo y desde dónde, que nadie puede editar ni borrar. Los demás administradores reciben avisos de cambios de configuración y de administradores.", "יומן פעילות של מי עשה מה, מתי ומאיפה, שאף אחד לא יכול לערוך או למחוק. מנהלי מערכת אחרים מקבלים התראה על שינויי הגדרות ומנהלים.")
add("Built and run carefully", "Construit et exploité avec soin", "Construido y operado con cuidado", "נבנה ומופעל בזהירות")
add("Runs as an ordinary user with no extra powers. New package versions wait two weeks, every package is checked, and independent security reviews come with fixes.", "Tourne en simple utilisateur, sans droits supplémentaires. Les nouvelles versions de paquets attendent deux semaines, chaque paquet est vérifié, et des revues de sécurité indépendantes sont suivies de correctifs.", "Funciona como usuario normal, sin poderes extra. Las nuevas versiones de paquetes esperan dos semanas, cada paquete se verifica y las revisiones de seguridad independientes vienen con correcciones.", "רץ כמשתמש רגיל בלי הרשאות נוספות. גרסאות חדשות של חבילות ממתינות שבועיים, כל חבילה נבדקת, וסקירות אבטחה עצמאיות מגיעות עם תיקונים.")

# Controls
add("Segregation of duties", "Séparation des tâches", "Segregación de funciones", "הפרדת תפקידים")
add("Nobody can both spend and sign off", "Personne ne peut à la fois dépenser et approuver", "Nadie puede gastar y aprobar a la vez", "אף אחד לא יכול גם להוציא וגם לאשר")
add("The controls auditors look for, built in rather than left to good intentions.", "Les contrôles que cherchent les auditeurs, intégrés plutôt que laissés à la bonne volonté.", "Los controles que buscan los auditores, integrados en lugar de dejados a la buena voluntad.", "הבקרות שהמבקרים מחפשים, מובנות במקום להישען על כוונות טובות.")
add("Controls and what they prevent", "Les contrôles et ce qu'ils empêchent", "Los controles y lo que evitan", "הבקרות ומה הן מונעות")
add("The control", "Le contrôle", "El control", "הבקרה")
add("What it prevents", "Ce qu'il empêche", "Lo que evita", "מה היא מונעת")
add("Nobody approves their own expenses", "Personne n'approuve ses propres dépenses", "Nadie aprueba sus propios gastos", "אף אחד לא מאשר את ההוצאות של עצמו")
add("An admin can allow accounting to self-approve when nobody else can, and those approvals are marked.", "Un administrateur peut autoriser la comptabilité à s'auto-approuver quand personne d'autre ne le peut, et ces approbations sont signalées.", "Un administrador puede permitir que contabilidad se autoapruebe cuando nadie más puede, y esas aprobaciones quedan marcadas.", "מנהל מערכת יכול לאפשר להנהלת החשבונות לאשר לעצמה כשאין אף אחד אחר, ואישורים כאלה מסומנים.")
add("Paying yourself without a second pair of eyes", "Se payer soi-même sans second regard", "Pagarte a ti mismo sin un segundo par de ojos", "לשלם לעצמך בלי זוג עיניים נוסף")
add("Two-step approval, if you want it", "Approbation en deux étapes, si vous le voulez", "Aprobación en dos pasos, si la quieres", "אישור דו-שלבי, אם רוצים")
add("The employee's manager first, then accounting.", "D'abord le manager de l'employé, puis la comptabilité.", "Primero el responsable del empleado, luego contabilidad.", "קודם המנהל של העובד, ואז הנהלת החשבונות.")
add("Payment without the person who knows the work seeing it", "Un paiement sans que la personne qui connaît le travail l'ait vu", "Un pago sin que lo vea quien conoce el trabajo", "תשלום בלי שמי שמכיר את העבודה ראה אותו")
add("Helping isn't approving", "Aider n'est pas approuver", "Ayudar no es aprobar", "לעזור זה לא לאשר")
add("Accounting can upload for an employee or act as them for up to 30 minutes (recorded under the accountant's own name, and the employee is told), but can never approve those receipts. Admins can't be acted as.", "La comptabilité peut déposer des reçus pour un employé ou agir en son nom jusqu'à 30 minutes (enregistré sous le nom du comptable, et l'employé est prévenu), mais ne peut jamais approuver ces reçus. On ne peut pas agir au nom d'un administrateur.", "Contabilidad puede subir tickets por un empleado o actuar como él hasta 30 minutos (queda registrado con el nombre del contable y el empleado recibe aviso), pero nunca puede aprobar esos tickets. No se puede actuar como un administrador.", "הנהלת החשבונות יכולה להעלות בשביל עובד או לפעול בשמו עד 30 דקות (נרשם בשם מנהלת החשבונות, והעובד מקבל הודעה), אבל אף פעם לא לאשר את הקבלות האלה. אי אפשר לפעול בשם מנהל מערכת.")
add("Creating an expense and approving it through someone else's account", "Créer une dépense et l'approuver via le compte de quelqu'un d'autre", "Crear un gasto y aprobarlo a través de la cuenta de otra persona", "ליצור הוצאה ולאשר אותה דרך החשבון של מישהו אחר")
add("Roles are guarded", "Les rôles sont protégés", "Los roles están protegidos", "התפקידים מוגנים")
add("Accountants add employees only. Only an admin makes managers, accountants and admins.", "Les comptables n'ajoutent que des employés. Seul un administrateur nomme managers, comptables et administrateurs.", "Los contables solo añaden empleados. Solo un administrador nombra responsables, contables y administradores.", "מנהלי חשבונות מוסיפים רק עובדים. רק מנהל מערכת ממנה מנהלים, מנהלי חשבונות ומנהלי מערכת.")
add("Accounting promoting itself or a friend", "La comptabilité qui se promeut elle-même ou un proche", "Contabilidad ascendiéndose a sí misma o a un amigo", "הנהלת חשבונות שמקדמת את עצמה או חבר")
add("You approve what you saw", "Vous approuvez ce que vous avez vu", "Apruebas lo que viste", "מאשרים את מה שראיתם")
add("If a receipt changes after you opened it, your decision is refused until you look again.", "Si un reçu change après que vous l'avez ouvert, votre décision est refusée jusqu'à ce que vous le regardiez à nouveau.", "Si un ticket cambia después de abrirlo, tu decisión se rechaza hasta que lo vuelvas a mirar.", "אם קבלה משתנה אחרי שפתחתם אותה, ההחלטה שלכם נדחית עד שתסתכלו שוב.")
add("Approving a different amount from the one you checked", "Approuver un autre montant que celui vérifié", "Aprobar un importe distinto del que revisaste", "לאשר סכום אחר מזה שבדקתם")
add("Flags must be looked at", "Les alertes doivent être examinées", "Los avisos hay que mirarlos", "חייבים להסתכל על הסימונים")
add("Approving a batch with a flagged receipt asks you to confirm you checked it.", "Approuver un lot contenant un reçu signalé vous demande de confirmer que vous l'avez vérifié.", "Aprobar un lote con un ticket marcado te pide confirmar que lo revisaste.", "אישור קבוצה עם קבלה מסומנת מבקש לאשר שבדקתם אותה.")
add("Waving a duplicate through in a batch", "Laisser passer un doublon dans un lot", "Colar un duplicado en un lote", "להעביר כפילות בתוך קבוצה")
add("Paid is paid", "Payé, c'est payé", "Pagado es pagado", "מה ששולם, שולם")
add("An exported receipt can't move month; taking back its approval or deleting it asks for confirmation.", "Un reçu exporté ne peut pas changer de mois ; retirer son approbation ou le supprimer demande une confirmation.", "Un ticket exportado no puede cambiar de mes; retirar su aprobación o borrarlo pide confirmación.", "קבלה שיוצאה לא עוברת חודש; ביטול האישור שלה או מחיקה דורשים אישור.")
add("Changing what was already sent for payment", "Modifier ce qui est déjà parti au paiement", "Cambiar lo que ya se envió a pagar", "לשנות את מה שכבר נשלח לתשלום")
add("Closing is final, reopening is recorded", "La clôture est définitive, la réouverture est tracée", "Cerrar es definitivo, reabrir queda registrado", "סגירה סופית, פתיחה מחדש מתועדת")
add("A month closes only when all is decided; reopening needs a reason that stays in its history.", "Un mois ne se clôture que lorsque tout est décidé ; le rouvrir demande un motif qui reste dans son historique.", "Un mes solo se cierra cuando todo está decidido; reabrirlo exige un motivo que queda en su historial.", "חודש נסגר רק כשהכול הוחלט; פתיחה מחדש דורשת סיבה שנשארת בהיסטוריה שלו.")
add("Late changes slipping into a closed month", "Des changements tardifs glissés dans un mois clôturé", "Cambios tardíos colándose en un mes cerrado", "שינויים מאוחרים שמתגנבים לחודש סגור")
add("Deleting leaves a trace", "Supprimer laisse une trace", "Borrar deja rastro", "מחיקה משאירה עקבות")
add("Only accounting deletes, with a reason; the employee is emailed and the history stays.", "Seule la comptabilité supprime, avec un motif ; l'employé reçoit un e-mail et l'historique reste.", "Solo contabilidad borra, con un motivo; el empleado recibe un email y el historial se conserva.", "רק הנהלת החשבונות מוחקת, עם סיבה; העובד מקבל מייל וההיסטוריה נשמרת.")
add("Receipts disappearing", "Des reçus qui disparaissent", "Tickets que desaparecen", "קבלות שנעלמות")
add("Admins watch each other", "Les administrateurs se surveillent mutuellement", "Los administradores se vigilan entre sí", "מנהלי המערכת שומרים זה על זה")
add("Settings and admin-role changes alert every other admin; a lone admin is reminded to add another.", "Les changements de réglages et de rôle administrateur alertent tous les autres administrateurs ; un administrateur seul est invité à en ajouter un autre.", "Los cambios de configuración y de rol de administrador avisan a todos los demás administradores; a un administrador solo se le recuerda añadir otro.", "שינויי הגדרות ותפקיד מנהל מערכת מתריעים לכל מנהלי המערכת האחרים; מנהל יחיד מקבל תזכורת להוסיף עוד אחד.")
add("One admin changing the rules unseen", "Un administrateur qui change les règles sans être vu", "Un administrador cambiando las reglas sin que nadie lo vea", "מנהל מערכת אחד שמשנה את הכללים בלי שאף אחד רואה")

# Setup wizard
add("The setup wizard", "L'assistant d'installation", "El asistente de configuración", "אשף ההתקנה")
add("Set up in your browser, not in config files", "Configuré dans votre navigateur, pas dans des fichiers", "Se configura en el navegador, no en archivos", "הגדרה בדפדפן, לא בקובצי הגדרות")
add("Open the app's address and a short wizard walks you through it. The first three steps are all you need; the rest can wait.", "Ouvrez l'adresse de l'application et un court assistant vous guide. Les trois premières étapes suffisent ; le reste peut attendre.", "Abre la dirección de la app y un breve asistente te guía. Los tres primeros pasos bastan; el resto puede esperar.", "פותחים את כתובת האפליקציה ואשף קצר מוביל אתכם. שלושת השלבים הראשונים הם כל מה שצריך; השאר יכול לחכות.")
add("Every step checks itself", "Chaque étape se vérifie", "Cada paso se comprueba", "כל שלב בודק את עצמו")
add("The database connection, a test file in storage, the email server: you know it works before you move on.", "La connexion à la base, un fichier test dans le stockage, le serveur de messagerie : vous savez que ça marche avant de continuer.", "La conexión a la base de datos, un archivo de prueba en el almacenamiento, el servidor de correo: sabes que funciona antes de seguir.", "החיבור למסד הנתונים, קובץ בדיקה באחסון, שרת המייל: יודעים שזה עובד לפני שממשיכים.")
add("Safe database logins, made for you", "Des accès à la base sûrs, créés pour vous", "Usuarios de base de datos seguros, creados por ti", "משתמשי מסד נתונים בטוחים, נוצרים בשבילכם")
add("Give it an admin login once and it creates a limited login for the app. The admin login isn't kept.", "Donnez-lui une fois un accès administrateur et il crée un accès limité pour l'application. L'accès administrateur n'est pas conservé.", "Dale una vez un usuario administrador y crea un usuario limitado para la app. El usuario administrador no se guarda.", "נותנים לו פעם אחת משתמש מנהל, והוא יוצר משתמש מוגבל לאפליקציה. משתמש המנהל לא נשמר.")
add("Moving to a new server?", "Vous changez de serveur ?", "¿Cambias de servidor?", "עוברים לשרת חדש?")
add("Load a configuration backup and the wizard brings back your settings, expense types and people.", "Chargez une sauvegarde de configuration et l'assistant restaure vos réglages, vos types de dépenses et vos collaborateurs.", "Carga una copia de la configuración y el asistente recupera tus ajustes, tipos de gasto y personas.", "טוענים גיבוי הגדרות, והאשף מחזיר את ההגדרות, סוגי ההוצאות והאנשים.")
add("Illustration: the setup wizard going through its seven steps", "Illustration : l'assistant d'installation parcourt ses sept étapes", "Ilustración: el asistente de configuración recorre sus siete pasos", "איור: אשף ההתקנה עובר על שבעת השלבים שלו")
add("Setup", "Installation", "Configuración", "התקנה")
add("File storage", "Stockage des fichiers", "Almacenamiento", "אחסון קבצים")
add("First admin", "Premier administrateur", "Primer administrador", "מנהל מערכת ראשון")
add("Sign-in", "Connexion", "Acceso", "כניסה")
add("later", "plus tard", "luego", "אחר כך")
add("Email", "E-mail", "Email", "מייל")
add("Branding", "Image de marque", "Marca", "מיתוג")
add("Connect a database", "Connecter une base de données", "Conectar una base de datos", "חיבור מסד נתונים")
add("Where Refund-Me keeps its data.", "Là où Refund-Me garde ses données.", "Donde Refund-Me guarda sus datos.", "איפה Refund-Me שומר את הנתונים שלו.")
add("Built-in", "Intégrée", "Integrada", "מובנה")
add("up to ~50 people", "jusqu'à ~50 personnes", "hasta ~50 personas", "עד כ-50 אנשים")
add("recommended", "recommandé", "recomendado", "מומלץ")
add("or Azure SQL", "ou Azure SQL", "o Azure SQL", "או Azure SQL")
add("Connect &amp; continue", "Connecter et continuer", "Conectar y seguir", "חיבור והמשך")
add("Where receipt files are kept", "Où sont gardés les fichiers des reçus", "Dónde se guardan los archivos", "איפה נשמרים קובצי הקבלות")
add("Photos, PDFs and logos.", "Photos, PDF et logos.", "Fotos, PDF y logotipos.", "תמונות, קובצי PDF ולוגואים.")
add("This server", "Ce serveur", "Este servidor", "השרת הזה")
add("a folder on the server", "un dossier sur le serveur", "una carpeta en el servidor", "תיקייה על השרת")
add("S3-compatible", "Compatible S3", "Compatible con S3", "תואם S3")
add("Check &amp; continue", "Vérifier et continuer", "Comprobar y seguir", "בדיקה והמשך")
add("Your company and the first admin", "Votre entreprise et le premier administrateur", "Tu empresa y el primer administrador", "החברה שלכם ומנהל המערכת הראשון")
add("Everything else can be edited later.", "Tout le reste peut être modifié plus tard.", "Todo lo demás se puede cambiar luego.", "את כל השאר אפשר לערוך אחר כך.")
add("Company name", "Nom de l'entreprise", "Nombre de la empresa", "שם החברה")
add("Acme Ltd", "Acme SARL", "Acme S.L.", "אקמה בע״מ")
add("Full name", "Nom complet", "Nombre completo", "שם מלא")
add("Noa Cohen", "Léa Dubois", "Carmen López", "נועה כהן")
add("Password", "Mot de passe", "Contraseña", "סיסמה")
add("Create and continue", "Créer et continuer", "Crear y seguir", "יצירה והמשך")
add("Let people sign in with their work account.", "Permettez la connexion avec le compte professionnel.", "Que la gente entre con su cuenta de trabajo.", "לאפשר כניסה עם חשבון העבודה.")
add("Email links and passwords only", "Liens par e-mail et mots de passe seulement", "Solo enlaces por email y contraseñas", "רק קישורים במייל וסיסמאות")
add("You can do this later", "Vous pouvez le faire plus tard", "Puedes hacerlo luego", "אפשר לעשות את זה אחר כך")
add("Outgoing email", "E-mail sortant", "Correo saliente", "מייל יוצא")
add("For invitations, sign-in links and reminders.", "Pour les invitations, les liens de connexion et les rappels.", "Para invitaciones, enlaces de acceso y recordatorios.", "להזמנות, קישורי כניסה ותזכורות.")
add("Mail server", "Serveur de messagerie", "Servidor de correo", "שרת מייל")
add("Sender", "Expéditeur", "Remitente", "שולח")
add("expenses@acme.example", "frais@acme.example", "gastos@acme.example", "expenses@acme.example")
add("Send a test email", "Envoyer un e-mail de test", "Enviar un email de prueba", "שליחת מייל בדיקה")
add("Your name, logo and colors on screens and reports.", "Votre nom, logo et couleurs sur les écrans et les rapports.", "Tu nombre, logotipo y colores en pantallas e informes.", "השם, הלוגו והצבעים שלכם על המסכים ובדוחות.")
add("Logo", "Logo", "Logotipo", "לוגו")
add("Reading receipts", "Lecture des reçus", "Lectura de tickets", "קריאת קבלות")
add("Built in, or something stronger when you want it.", "Intégrée, ou plus puissante quand vous le voulez.", "Integrada, o algo más potente cuando quieras.", "מובנית, או משהו חזק יותר כשרוצים.")
add("Built in", "Intégrée", "Integrada", "מובנית")
add("nothing leaves the server", "rien ne quitte le serveur", "nada sale del servidor", "שום דבר לא יוצא מהשרת")
add("Your GPU server", "Votre serveur GPU", "Tu servidor GPU", "שרת GPU שלכם")
add("Cloud AI", "IA cloud", "IA en la nube", "AI בענן")
add("off until you confirm", "désactivée tant que vous ne confirmez pas", "apagada hasta que confirmes", "כבוי עד שמאשרים")
add("Try the sample receipt", "Tester le reçu d'exemple", "Probar el ticket de ejemplo", "בדיקה על הקבלה לדוגמה")
add("Ready", "Prêt", "Listo", "מוכן")
add("Invite your people and start scanning.", "Invitez vos collaborateurs et commencez à photographier.", "Invita a tu gente y empieza a escanear.", "מזמינים את העובדים ומתחילים לסרוק.")

# Install
add("Installation", "Installation", "Instalación", "התקנה")
add("Running in minutes", "Opérationnel en quelques minutes", "En marcha en minutos", "עובד תוך דקות")
add("One command on a server with Docker. A setup wizard in the browser does the rest. Free for your own company (", "Une commande sur un serveur avec Docker. Un assistant dans le navigateur fait le reste. Gratuit pour votre propre entreprise (", "Un comando en un servidor con Docker. Un asistente en el navegador hace el resto. Gratis para tu propia empresa (", "פקודה אחת על שרת עם Docker. אשף בדפדפן עושה את השאר. חינם לחברה שלכם (")
add("license", "licence", "licencia", "רישיון")
add("# one command: settings, key, download, start", "# une commande : réglages, clé, téléchargement, démarrage", "# un comando: ajustes, clave, descarga, arranque", "# פקודה אחת: הגדרות, מפתח, הורדה, הפעלה")
add("# then open the setup wizard", "# puis ouvrez l'assistant d'installation", "# luego abre el asistente de configuración", "# ואז פותחים את אשף ההתקנה")
add("# upgrading later", "# mise à jour plus tard", "# actualizar más adelante", "# עדכון בהמשך")
add("You need", "Il vous faut", "Necesitas", "מה צריך")
add("A Linux server or virtual machine with Docker. 2 CPU cores and 2 GB of memory are enough for a small office.", "Un serveur Linux ou une machine virtuelle avec Docker. 2 cœurs et 2 Go de mémoire suffisent pour un petit bureau.", "Un servidor Linux o una máquina virtual con Docker. 2 núcleos y 2 GB de memoria bastan para una oficina pequeña.", "שרת לינוקס או מכונה וירטואלית עם Docker. 2 ליבות ו-2 GB זיכרון מספיקים למשרד קטן.")
add("A database: the built-in one (up to about 50 people), or PostgreSQL, SQL Server / Azure SQL, MySQL or MariaDB.", "Une base de données : celle intégrée (jusqu'à environ 50 personnes), ou PostgreSQL, SQL Server / Azure SQL, MySQL ou MariaDB.", "Una base de datos: la integrada (hasta unas 50 personas), o PostgreSQL, SQL Server / Azure SQL, MySQL o MariaDB.", "מסד נתונים: המובנה (עד כ-50 אנשים), או PostgreSQL,‏ SQL Server / Azure SQL,‏ MySQL או MariaDB.")
add("An HTTPS address in front of the app for real use.", "Une adresse HTTPS devant l'application pour un usage réel.", "Una dirección HTTPS delante de la app para uso real.", "כתובת HTTPS מול האפליקציה לשימוש אמיתי.")
add("Optional: an email server, and Microsoft Entra ID or Google Workspace for single sign-on.", "En option : un serveur de messagerie, et Microsoft Entra ID ou Google Workspace pour l'authentification unique.", "Opcional: un servidor de correo, y Microsoft Entra ID o Google Workspace para el inicio de sesión único.", "אופציונלי: שרת מייל, ו-Microsoft Entra ID או Google Workspace לכניסה אחודה.")
add("The full guide for IT, Coolify included:", "Le guide complet pour l'informatique, Coolify compris :", "La guía completa para TI, Coolify incluido:", "המדריך המלא ל-IT, כולל Coolify:")
add("the install repository", "le dépôt d'installation", "el repositorio de instalación", "מאגר ההתקנה")
add("Give your people their evenings back", "Rendez leurs soirées à vos collaborateurs", "Devuélvele las tardes a tu gente", "תחזירו לעובדים את הערבים שלהם")
add("Receipts in, reimbursements out, with the controls your auditors expect. Installed on your server, in Hebrew and English, on every device.", "Des reçus en entrée, des remboursements en sortie, avec les contrôles qu'attendent vos auditeurs. Installé sur votre serveur, en hébreu et en anglais, sur tous les appareils.", "Entran tickets, salen reembolsos, con los controles que esperan tus auditores. Instalado en tu servidor, en hebreo e inglés, en todos los dispositivos.", "קבלות נכנסות, החזרים יוצאים, עם הבקרות שהמבקרים מצפים להן. מותקן על השרת שלכם, בעברית ובאנגלית, בכל מכשיר.")
add("Refund-Me · expense reimbursement for Israeli companies", "Refund-Me · remboursement de notes de frais pour les entreprises israéliennes", "Refund-Me · reembolso de gastos para empresas israelíes", "Refund-Me · החזר הוצאות לחברות בישראל")
add("· The illustrations use made-up data.", "· Les illustrations utilisent des données fictives.", "· Las ilustraciones usan datos inventados.", "· האיורים משתמשים בנתונים בדויים.")

# --- The license summary pages -----------------------------------------------------------------
LICENSE = {
    "fr": {
        "lang": "fr", "title": "Licence Refund-Me", "desc": "Les conditions d'utilisation de Refund-Me : gratuit pour votre propre entreprise, pas pour la revente.",
        "back": "← Retour au site", "eyebrow": "Licence",
        "short": "En bref : gratuit pour votre propre entreprise, pas pour la revente.",
        "summary": "Toute entreprise peut installer Refund-Me et l'utiliser pour ses propres dépenses, gratuitement. Vous ne pouvez pas le vendre, le redistribuer ni l'exploiter comme service pour d'autres entreprises sans autorisation. Il est fourni tel quel, et vos données restent les vôtres.",
        "binding": "Ce résumé est une traduction de courtoisie. Seul le texte anglais ci-dessous fait foi.",
        "terms": "Le texte complet (en anglais)",
    },
    "es": {
        "lang": "es", "title": "Licencia de Refund-Me", "desc": "Las condiciones de uso de Refund-Me: gratis para tu propia empresa, no para reventa.",
        "back": "← Volver al sitio", "eyebrow": "Licencia",
        "short": "En resumen: gratis para tu propia empresa, no para reventa.",
        "summary": "Cualquier empresa puede instalar Refund-Me y usarlo para sus propios gastos, gratis. No puedes venderlo, redistribuirlo ni ofrecerlo como servicio a otras empresas sin permiso. Se entrega tal cual, y tus datos siguen siendo tuyos.",
        "binding": "Este resumen es una traducción de cortesía. Solo el texto en inglés de abajo es vinculante.",
        "terms": "El texto completo (en inglés)",
    },
    "he": {
        "lang": "he", "title": "רישיון Refund-Me", "desc": "תנאי השימוש ב-Refund-Me: חינם לחברה שלכם, לא למכירה חוזרת.",
        "back": "→ חזרה לאתר", "eyebrow": "רישיון",
        "short": "בקצרה: חינם לחברה שלכם, לא למכירה חוזרת.",
        "summary": "כל חברה יכולה להתקין את Refund-Me ולהשתמש בו להוצאות שלה, בחינם. אסור למכור אותו, להפיץ אותו מחדש או להפעיל אותו כשירות לחברות אחרות בלי רשות. הוא מסופק כמות שהוא, והמידע שלכם נשאר שלכם.",
        "binding": "התקציר הזה הוא תרגום לנוחות בלבד. רק הנוסח באנגלית שלמטה מחייב.",
        "terms": "הנוסח המלא (באנגלית)",
    },
}
LICENSE["fr"] = {k: (fr_typo(v) if k not in ("lang",) else v) for k, v in LICENSE["fr"].items()}


def translate_landing(src: str, lang: str):
    """Translates every text and label of the English page; returns (html, missing texts)."""
    tr, money, missing = T[lang], MONEY[lang], []
    # Leave styles and scripts alone.
    keep_blocks = []

    def stash(m):
        keep_blocks.append(m.group(0))
        return f"\x00{len(keep_blocks) - 1}\x00"

    work = re.sub(r"<style>.*?</style>|<script>.*?</script>", stash, src, flags=re.S)
    parts = re.split(r"(<[^>]+>)", work)
    prev_tag = ""
    for i, part in enumerate(parts):
        if part.startswith("<"):
            def attr(m):
                name, value = m.group(1), m.group(2)
                if value in tr:
                    return f'{name}="{tr[value]}"'
                if re.search("[A-Za-z]{2}", value) and value not in KEEP and not value.startswith(("http", "width")):
                    missing.append(value)
                return m.group(0)

            if part.startswith(("<meta name=\"description\"",)) or "aria-label=" in part:
                part = re.sub(r'(aria-label|content)="([^"]+)"', attr, part)
                parts[i] = part
            prev_tag = part
            continue
        core = part.strip()
        if not core or "\x00" in core:
            continue
        lead, trail = part[: len(part) - len(part.lstrip())], part[len(part.rstrip()):]
        if core in tr:
            new = tr[core]
        elif core in money:
            new = money[core]
        elif core == "$" and prev_tag != '<span class="p">':
            new = MARK[lang]
        elif core in KEEP or not re.search("[A-Za-z]", core) or core in ("EN", "English", "French", "Spanish", "Hebrew"):
            continue
        else:
            missing.append(core)
            continue
        parts[i] = lead + new + trail
    out = "".join(parts)
    out = re.sub("\x00(\\d+)\x00", lambda m: keep_blocks[int(m.group(1))], out)
    # Language, direction, and the switcher for this language.
    out = out.replace('<html lang="en">', f'<html lang="{lang}"' + (' dir="rtl">' if lang == "he" else ">"), 1)
    out = re.sub(r'<div class="lang">.*?</ul>\s*</div>', switcher(lang, "index.html"), out, count=1, flags=re.S)
    return out, missing


def build_license(src: str, lang: str) -> str:
    L = LICENSE[lang]
    out = src.replace('<html lang="en">', f'<html lang="{lang}"' + (' dir="rtl">' if lang == "he" else ">"), 1)
    out = out.replace("<title>Refund-Me License</title>", f"<title>{L['title']}</title>", 1)
    out = re.sub(r'(<meta name="description" content=")[^"]*(">)', lambda m: m.group(1) + L["desc"] + m.group(2), out, count=1)
    out = out.replace('<a class="back" href="./">← Back to the site</a>', f'<a class="back" href="./">{L["back"]}</a>', 1)
    out = out.replace('<span class="mark">$</span>', f'<span class="mark">{MARK[lang]}</span>', 1)
    out = out.replace('<span class="eyebrow">License</span>', f'<span class="eyebrow">{L["eyebrow"]}</span>', 1)
    out = re.sub(r'<div class="summary">.*?</div>',
                 f'<div class="summary">\n    <b>{L["short"]}</b>\n    <span>{L["summary"]}</span>\n    <span class="binding">{L["binding"]}</span>\n  </div>\n  <h2 class="terms-title">{L["terms"]}</h2>',
                 out, count=1, flags=re.S)
    out = out.replace('<h1>Refund-Me License 1.0</h1>', '<h1 lang="en" dir="ltr">Refund-Me License 1.0</h1>', 1)
    out = out.replace('<p class="sub">', '<p class="sub" lang="en" dir="ltr">', 1)
    out = out.replace('<div class="doc">', '<div class="doc" lang="en" dir="ltr">', 1)
    out = out.replace('<p class="note">', '<p class="note" lang="en" dir="ltr">', 1)
    out = re.sub(r'<div class="lang">.*?</ul>\s*</div>', switcher(lang, "license.html"), out, count=1, flags=re.S)
    return out


def main() -> int:
    landing = (DOCS / "index.html").read_text(encoding="utf-8")
    license_en = (DOCS / "license.html").read_text(encoding="utf-8")
    problems = 0
    for lang in ("fr", "es", "he"):
        html, missing = translate_landing(landing, lang)
        if missing:
            problems += len(missing)
            print(f"[{lang}] no translation for:", file=sys.stderr)
            for m in dict.fromkeys(missing):
                print(f"  {m!r}", file=sys.stderr)
            continue
        folder = DOCS / lang
        folder.mkdir(exist_ok=True)
        (folder / "index.html").write_text(html, encoding="utf-8")
        (folder / "license.html").write_text(build_license(license_en, lang), encoding="utf-8")
        print(f"[{lang}] docs/{lang}/index.html, docs/{lang}/license.html")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
