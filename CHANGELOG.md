# What's new

Each version is published as `ghcr.io/oriyahoo/refund-me:<version>` (and `:latest`). To
upgrade: `docker compose pull && docker compose up -d` in your `refund-me` folder. Database
changes apply themselves on start; take a backup first.

## 0.3.6

- **Outgoing email through a webhook.** Admin → System → Outgoing email (and the setup wizard's
  Email step) now asks how to send: a mail server (SMTP), as before, or a webhook, for when your
  email goes out through an automation tool such as n8n or Make rather than a mail server the
  app can log in to. Each email is posted to the webhook's address as JSON (`sender`,
  `recipient`, `subject`, and `message` as HTML) with your key in the `x-api-key` header. "Send
  a test" tries it before anything is saved, and saving asks you to confirm it's you. A mail
  server and a webhook can both be saved; the one saved last is the one in use. The address must
  be `https`. See INSTALL.md → "Outgoing email through a webhook".
- **What the other side answered, in the activity log.** Each email's entry (Activity log →
  Emails → Details) now shows how it went out and the answer: the mail server's reply, the
  message id and the recipients it accepted or refused, or the webhook's status and its report.
  A failed email keeps the refusal next to the error.
- **The webhook in the configuration backup.** Saved and restored with the rest; its key is kept
  only when the server is the same.

## 0.3.5

- **Amazon S3 storage works.** Testing or moving to Amazon S3 failed with "HTTP 501
  NotImplemented": uploads went out without their size, which Amazon S3 refuses (Cloudflare R2
  and MinIO accept it). They now carry it.

## 0.3.4

- **Receipt numbers in the expense report.** The PDF report has a receipt-number column after the
  supplier, in place of the description column.

## 0.3.3

- **Parking receipts need no description.** An expense whose type is parking (חניה, Parking,
  Stationnement, Estacionamiento) can be saved and submitted with the description empty; every
  other type still needs one.
- **No zooming the page on phones.** Pinch and double-tap no longer zoom the app's pages; the
  receipt viewer still zooms the receipt (pinch, double-tap, the + and − buttons).
- **The version once.** On phones the profile page showed the version twice.

## 0.3.2

- **Flags in the language menu.** The globe shows a small flag of the app's current language, and
  its menu lists the languages by their flags (the language's name shows on hover and is read out
  by screen readers).

## 0.3.1

- **HTTPS from the app itself.** `HTTPS=self-signed` (the installer's `--https`, also offered when
  you choose Cloudflare's proxy): the app makes its own certificate on first start and answers
  HTTPS only, on the same port. For Cloudflare's proxy in SSL/TLS mode "Full" when nothing else on
  the server handles HTTPS. Or give it your own certificate with `TLS_CERT_FILE` and
  `TLS_KEY_FILE` (a Cloudflare Origin Certificate works with "Full (strict)").
- **A newer PDF reader** (pdf.js 6.5). Some PDF receipts that took long to open, or didn't open,
  are read right away.
- **The Refund-Me logo** in the browser tab and as the icon of the installed app.
- **Log forwarding in the configuration backup.** The SIEM / Axiom settings are saved and
  restored with the rest; a token is kept only when the destination is the same.
- **Installer: choose the port.** A first install in a terminal now also asks for the port on the
  server (Enter keeps 3855). A number outside 1-65535, or a port something else already uses, is
  refused before anything starts; `--port` is checked the same way. Changing only the port of an
  install published on `127.0.0.1` (Cloudflare Tunnel) keeps it on `127.0.0.1`.

## 0.3.0

- **Log forwarding to your SIEM** (Admin → System → Log forwarding). Every activity-log entry
  also goes, as it happens, to your SIEM or log service: syslog (RFC 5424, over TLS, TCP or UDP)
  and/or HTTPS as JSON, with a ready choice for **Axiom**. Entries include the person's name and
  email and the address they came from; passwords and keys never. "Check and save" sends a test
  entry first. Turning it on, changing it or turning it off asks you to confirm it's you, and
  the other admins are told. While the destination is down, entries wait and are sent again.
- **Errors in the activity log.** A page, action or background task that fails is recorded under
  the new **Errors** kind, with the technical detail IT needs (passwords removed). The same error
  repeating is recorded once, with how many times it happened.
- **Amounts in French and Spanish are read correctly.** In 0.2.0 an amount typed with a decimal
  comma ("45,90") was saved as 4,590.00. Please check any expense entered in French or Spanish
  on 0.2.0 before approving it.
- **Receipts in other currencies:**
  - All 15 currencies are recognised on receipts; a "$" with Canadian or Australian details is
    read as CAD or AUD, and an unclear sign is left for the employee instead of guessed.
  - The currency and total read from the receipt are kept: changing them is flagged for the
    approver, as are a receipt with no exchange rate and a rate typed by hand (with who typed it).
  - A rate typed by hand more than 10% away from the bank's needs a reason.
  - No VAT on a receipt in another currency, and none in the export's VAT column.
  - Exports have six new columns: receipt currency, receipt total, exchange rate, rate date,
    rate source and the converted amount.
  - Missing rates are filled in automatically once the sources answer again, also for older
    receipts.
  - The company currency can't be changed once there are expenses (also when loading a
    configuration backup).
- **Faster pages:** each page sends the browser only its own texts (the sign-in page is about
  95 KB lighter).
- **Installer:** `--cloudflare` now trusts only Cloudflare's own addresses, and a new
  `--cloudflare-tunnel` keeps the port on the server itself. All settings live in `.env`, so
  running the installer again keeps them (a `docker-compose.yml` you changed is kept, the new one
  saved next to it); run with options it changes only those settings, and before an upgrade it
  asks first. The install folder is private to its owner.
- **Your company's own certificate authority** for a database, mail server or SIEM: see
  INSTALL.md (`NODE_EXTRA_CA_CERTS`).
- **Third-party licences:** THIRD_PARTY_NOTICES.txt, in the image and with each release.
- Database: three new columns that can be empty, added in moments on every database.

## 0.2.0

- **French and Spanish.** The whole app, its Help, emails and PDF reports, in Hebrew, English,
  French and Spanish. The globe opens a language menu; each person picks their own, and a
  company can make any of them its default. Dates and amounts follow the language (1 234,56 €).
- **Receipts in other currencies.** A receipt from abroad is converted at the official rate of
  its date: the Bank of Israel's for a shekel company, the European Central Bank's otherwise.
  The converted amount is proposed as the refund; if the card charged a different amount, the
  employee enters that and accounting sees the difference before approving.
- **Exchange rates page** (Admin → Exchange rates, accounting): the latest rates and their source,
  "Fetch rates now", and rates entered or corrected by hand. Rates are fetched every few hours;
  the server needs outgoing access to edge.boi.gov.il and www.ecb.europa.eu, or rates are entered
  by hand.
- **15 company currencies** (ILS, USD, EUR, GBP, CHF, JPY, CAD, AUD, SEK, NOK, DKK, PLN, CZK, HUF,
  CNY).
- **French and Spanish receipts:** the built-in reader reads the company's language and English;
  decimal commas, TOTAL TTC, TOTAL A PAGAR, TVA and IVA are understood. Expense types can have
  French and Spanish names.
- **Powered by Refund-Me** under the company's logo in the menu.
- The cloud AI receipt test names the provider that read the sample.


## 0.1.2

- **Debian 13.** The image now runs on Debian 13 (trixie), the current Debian release with full
  security support, instead of Debian 12. Node.js stays at version 22. Nothing to change on your
  side: `docker compose pull && docker compose up -d`.
- Each release is now checked before it's published: PDF rendering (Hebrew and English) and the
  image, canvas and database components are tested inside the image.

## 0.1.1

- **English by default.** A new install's setup wizard opens in English, and English is the
  company's preselected language. Hebrew is one click away in the wizard, and everyone can still
  switch their own language with the globe icon. Existing installs keep the language they chose.
- Emails and alerts sent where no language is known (sign-in links, security notices, settings
  alerts) are in English.

## 0.1.0

The first public release.

- **Receipts:** scan with the phone camera, many in a row, or upload photos and PDFs (HEIC from
  iPhones too). The app reads the business name and ID, date, total, VAT and receipt number, in
  Hebrew and English, on your own server.
- **Months:** each month is a report with a due day, reminders, and a clear status for every
  receipt: ready, needs you, handed in, approved, returned.
- **Approvals:** accounting only, or the employee's manager first; approve one, several or a
  whole month; return with a note; take an approval back; close and reopen months.
- **Flags:** possible duplicates, over a type's monthly limit, large invoices without an
  allocation number, changes after handing in, foreign currency.
- **Exports:** Excel and CSV with each expense type's account (GL) code, and branded PDF reports
  per employee, with the receipt photos if you want them.
- **Controls:** no approving your own expenses, two-step approval, helping without approving,
  guarded roles, an activity log nobody can edit, settings alerts to admins.
- **Sign-in:** Microsoft or Google work accounts, one-time email links, or passwords; only
  people on the list get in.
- **Every device:** phone, tablet and computer; install it on the home screen from the
  `/install` page; Hebrew and English; light, dark, navy and warm themes.
- **Optional:** cloud AI or your own GPU server for receipt reading, AI assistants (Claude,
  Cursor, VS Code) through MCP, configuration backups and restore points.
- **Databases:** built-in, PostgreSQL, SQL Server / Azure SQL, MySQL / MariaDB.
