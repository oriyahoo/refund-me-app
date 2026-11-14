# What's new

Each version is published as `ghcr.io/oriyahoo/refund-me:<version>` (and `:latest`). To
upgrade: `docker compose pull && docker compose up -d` in your `refund-me` folder. Database
changes apply themselves on start; take a backup first.

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
