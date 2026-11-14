# Refund-Me

**Snap the receipt. Get paid back. No paper, no chasing, no spreadsheets.**

Refund-Me is expense reimbursement for Israeli companies. Employees photograph receipts on their
phone, the app reads them (in Hebrew, English, French and Spanish), managers and accounting approve with a tap,
and the month goes to the accounting system as Excel, CSV or a branded PDF. It runs on your own
server, so your receipts and your people's details never leave the company.

**[See the website →](https://oriyahoo.github.io/refund-me-app/)** · [Install](#installation) ·
[What's new](CHANGELOG.md) · Free to use for your own company ([license](LICENSE))

---

## Why companies choose Refund-Me

| The old way | With Refund-Me |
|---|---|
| Receipts lost in wallets and car seats | A photo the moment you pay. The app keeps it. |
| Typing amounts, dates and VAT numbers into Excel | The app reads the business name and ID, date, total, VAT and receipt number for you |
| "Did you get my expenses?" emails | Everyone sees where their month stands: waiting, approved, returned |
| Accounting chasing people at month end | Automatic reminders before the due day, and one click to remind everyone |
| Checking every receipt by eye for mistakes | The app flags what deserves a look: possible duplicates, over-the-limit amounts, missing details |
| Re-typing everything into the accounting system | Export the month with each expense type's account (GL) code, ready to import |

## How it works

1. **Snap.** Open the app on your phone and scan receipts one after another, or upload photos and PDFs.
2. **Check.** The app fills in the details. You glance at them, fix anything it misread, and hand in the month.
3. **Approve.** Your manager approves (if your company wants that step), then accounting. Anything wrong comes back to you with a note.
4. **Export.** Accounting closes the month and exports it: Excel or CSV for the accounting system, and a branded PDF report per employee, with the receipt photos if you want them.

## Something for everyone

**Employees**
- Scan receipts with the phone camera, many in a row, or upload photos and PDFs (HEIC from iPhones too).
- Back from a trip abroad? Receipts in another currency are converted at the official rate of their date (Bank of Israel, or the European Central Bank); if your card charged a little more, enter that and accounting sees the difference.
- See each month at a glance: total, what's ready, what needs you, what's handed in.
- Returned receipts come back with a note saying what to fix.
- Personal Insights: where your money went this year.

**Managers**
- One email per employee and month when there's something to approve.
- Approve a whole month or single receipts; return with a note.
- Team view in Insights.

**Accounting**
- One page with everyone's months: who handed in, what waits, totals and flags.
- Approve one, several or a whole month; take an approval back; close and reopen months.
- Exports for the accounting system and branded PDF reports.
- Help an employee by uploading for them or opening the app as them (within strict rules, below).
- Manage expense types (with account codes and monthly limits), employees and the submission policy.

**Admins**
- Your company's name, logo and colors on every screen and report.
- Sign-in with Microsoft or Google work accounts, email links or passwords.
- A complete activity log, settings alerts, backups and restore points.
- Optional AI assistants (Claude, Cursor, VS Code and others) that look up and act on expenses with each person's own permissions ([below](#ask-your-ai-assistant)).

## Ask your AI assistant

Refund-Me works with AI assistants such as Claude, Cursor and VS Code, and any other assistant
that supports MCP (the standard way for assistants to use apps). Connect it once, then just ask:

- **Employees:** "What's still missing in my June?" · "Change the taxi receipt's date to the 3rd." · "Submit my month."
- **Managers:** "What's waiting for my approval?" · "Show me Dana's October and approve it."
- **Accounting:** "Who hasn't handed in November?" · "How much did Sales spend on fuel this year?" · "Export November to Excel." · "Remind everyone."
- **Admins:** "Who changed the settings this week?"

**Safe by design**
- **The assistant is you, not more.** It works with a personal token and gets exactly your permissions: an employee's assistant sees only their own expenses.
- **Nothing changes by surprise.** Submitting, approving, closing a month or deleting shows a preview first and needs a confirmation; flagged receipts must be looked at before approval, as in the app.
- **You choose how far it goes.** Tokens can be read-only, expire after 30, 90 or 365 days, and can be revoked one by one or all at once.
- **Admins decide.** It's off until an admin turns it on, for the roles they choose. Receipt photos aren't shared with assistants unless an admin allows it.
- **Recorded.** Every assistant action is in the activity log, under the person's name.
- **Good to know:** what the assistant reads goes to the AI service you use (Anthropic, OpenAI and so on), under that service's terms. That's why it's off by default.

## Works on every device

Refund-Me is built for the phone first and is just as comfortable on a tablet or a big screen.

- **Phones:** a menu bar at the bottom within thumb's reach, the camera one tap away, big buttons. Press and hold a receipt or a person for the same menu a right-click gives on a computer.
- **Tablets:** the same app with more room.
- **Computers:** the list and the selected receipt side by side, headers and filters that stay in view while you scroll, and right-click menus.
- **Install it like an app:** add it to the home screen on iPhone, iPad or Android and it opens full screen with its own icon. No app store needed. Your app's `/install` page shows how, step by step, with animations: send your people the link.
- **Hebrew, English, French and Spanish,** each person in their own language, with proper right-to-left screens in Hebrew.
- **Your look:** light, dark, navy or warm, the same on all your devices.

## Your data stays yours

- **On your own server.** One install per company, on your server or your cloud account. You own the database and the files.
- **No internet needed.** Receipts are read on the server itself, and PDF reports are made there too. The only thing it fetches is the day's exchange rates (just currency codes and dates are sent), and accounting can enter those by hand instead.
- **Cloud AI only if you choose it.** For even better reading you can connect an AI provider (Anthropic, OpenAI, xAI, OpenRouter) or your own GPU server. It's off until an admin turns it on and confirms, because receipt photos would then go to that provider.
- **Less kept, less at risk.** The raw text read from receipts is deleted after 30 days; the receipt, its details and the photo stay.
- **Your choice of database:** the built-in one for small offices, or PostgreSQL, SQL Server, MySQL or MariaDB.

## Security, in plain words

Expense apps handle money and personal details: names, amounts, and receipt photos that can show
card digits and car plates. Here is what protects them.

**Who gets in**
- **Only people on the list can sign in.** Someone with a company Microsoft account who isn't on the list waits for approval.
- **Sign in the way your company already works:** Microsoft or Google work accounts, a one-time email link, or a password.
- **Guessing passwords doesn't work:** after a few wrong tries, password sign-in pauses for a while, and someone whose account is being targeted gets an email.
- **Sensitive changes need a fresh sign-in.** Making someone an admin, changing an admin's email, the sign-in or mail settings, resetting data, or loading a backup all ask the admin to prove it's really them (a recent sign-in or their password). A stolen open session isn't enough.

**What each person can see and do**
- Everyone sees only what their role allows: employees their own expenses, managers their team, accounting the company.
- AI assistants connect with a personal token and get exactly the permissions of the person who made it, never more. Tokens can be read-only and can be revoked at once, one or all.

**Keeping secrets secret**
- Passwords and keys saved in the settings (database, email, sign-in apps, AI providers) are encrypted. The key can be kept apart from the data, so a copy of the data alone reveals nothing.
- **Least privilege for the database:** the setup wizard creates a separate login for the running app that can read and write the app's data only. It can't create or drop tables, and has no rights on the rest of the database server.
- The app answers only on the addresses it's set up for, and its pages run only the app's own code.

**Built and run carefully**
- The app runs as an ordinary user inside its container, with no extra powers, and can only write to its data folder.
- New versions of the building blocks it uses are taken only once they've been out for two weeks, every package is checked against its published fingerprint, and the packages are scanned for known security problems.
- Independent security reviews of the whole app, in several rounds, each followed by fixes.
- Every image comes with a list of what's inside it and a signed record of how it was built, so you can check it came from here.

**Nothing happens quietly**
- **An activity log** records who did what and when: sign-ins, receipts, approvals, settings, emails, exports and AI assistant calls, with the network address it came from. Entries can't be edited or deleted.
- **Admins are alerted** in the app when someone changes a setting or gives or takes away the admin role, with what changed and from where.
- **Backups and restore points** for the settings, and a safe way back in if the only admin is gone.

## Segregation of duties, in plain words

Good expense control means no single person can both spend and sign off, and nobody can quietly
undo a decision. Refund-Me builds that in:

| Control | What it prevents |
|---|---|
| **Nobody approves their own expenses.** (An admin can allow accounting to self-approve when nobody else can; such approvals are marked "self-approved".) | Paying yourself without a second pair of eyes |
| **Two-step approval if you want it:** the employee's manager first, then accounting. | A receipt reaching payment without the person who knows the work seeing it |
| **Helping isn't approving.** Accounting can upload receipts for an employee or open the app as them (30 minutes at most, recorded under the accountant's own name, and the employee is told), but can never approve those receipts, and can't approve, return or change settings while acting. Admins' accounts can't be acted as at all. | Creating an expense and approving it yourself through someone else's account |
| **Roles are guarded.** Accountants can add employees only. Only an admin can make someone a manager, accountant or admin. | Accounting promoting itself or a friend |
| **You approve what you saw.** If an employee changes a receipt after you opened it, your decision is refused until you look again. | Approving a different amount from the one you checked |
| **Flags must be looked at.** Approving several receipts when one is flagged asks you to confirm you checked the flagged ones. | Waving through a duplicate or over-the-limit receipt in a batch |
| **Paid is paid.** A receipt that already went out in an export can't move to another month, and taking back its approval or deleting it asks for confirmation. | Changing what was already sent for payment without noticing |
| **Closing is final, reopening is recorded.** A month closes only when everything in it is decided; reopening needs a reason, which stays in the month's history. | Late changes slipping into a closed month |
| **Deleting leaves a trace.** Only accounting can delete a receipt, with a reason; the employee is emailed, and the history stays in the activity log. | Receipts disappearing |
| **Admins watch each other.** Settings and admin-role changes alert every other admin, and the app reminds you while you have only one admin. | One admin changing the rules unseen |

## Installation

Refund-Me runs as a single Docker container. Whoever looks after your servers can have it running
in minutes; a setup wizard in the browser does the rest.

**You need**
- A Linux server (or virtual machine) with Docker and Docker Compose. 2 CPU cores and 2 GB of memory are enough for a small office.
- A database: the built-in one (up to about 50 people, nothing to install), or PostgreSQL 15+ (recommended), SQL Server 2017+ / Azure SQL, MySQL 8+ / MariaDB 10.6+.
- For real use: an HTTPS address in front of the app.
- Optional: an email server for invitations and reminders, and Microsoft Entra ID or Google Workspace for single sign-on.

**Install with one command**

```sh
curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/install.sh | sh
```

It creates a `refund-me` folder with the settings and an encryption key, downloads the app and
starts it. Run in a terminal, it asks two quick questions: the address people will use, and
whether they reach it through Cloudflare or another proxy. Prefer to read a script before running
it? [Read install.sh](install.sh), or follow the [manual steps](INSTALL.md#quick-start).

**Behind Cloudflare or a proxy?** Say so, and the activity log and the sign-in limits see each
person's own address instead of the proxy's:

```sh
curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/install.sh | sh -s -- \
  --url https://expenses.company.com --cloudflare
```

| Option | What it does |
|---|---|
| `--url <address>` | The address people will use (for links in emails and sign-in) |
| `--cloudflare` | People come through Cloudflare (its proxy or a Cloudflare Tunnel) |
| `--proxy-ip <list>` | Your reverse proxy's address or range (nginx, Traefik, Coolify...), e.g. `172.18.0.0/16` |
| `--postgres` | Also run a bundled PostgreSQL database |
| `--port <n>` | The port on this server (default 3855) |
| `--dir <path>` | Where to install (default `./refund-me`) |
| `--no-prompt` / `--no-start` | Ask nothing / prepare the folder without starting |

All of these end up in `.env`, which you can edit any time (then `docker compose up -d`).

Then open `http://<your-server>:3855`. The setup wizard asks for the database, where to keep
receipt files and the first admin; then sign-in, email, your branding and how receipts are read.
Invite your people, and they're ready to scan.

**Upgrade**

```sh
cd refund-me && docker compose pull && docker compose up -d
```

Database changes apply themselves on start (take a backup first). What each version brings is in
[CHANGELOG.md](CHANGELOG.md). To stay on a version until you choose, set `REFUND_ME_VERSION` in
`.env`.

**Check what you install.** Every image is built here, in the open
([the release workflow](.github/workflows/release.yml)), with a signed record of how:

```sh
gh attestation verify oci://ghcr.io/oriyahoo/refund-me:latest --repo oriyahoo/refund-me-app
```

**More**
- The full guide for IT: [INSTALL.md](INSTALL.md): least-privilege database logins, HTTPS, single sign-on, reading receipts, Coolify, upgrades, backups, troubleshooting.
- Connecting AI assistants: [MCP.md](MCP.md).

## License

Free for any company to install and use for its own expenses. Not for resale: you may not sell
it, redistribute it, or run it as a service for other companies. The full terms are in
[LICENSE](LICENSE).

## Questions and problems

Open an [issue](https://github.com/oriyahoo/refund-me-app/issues). Please don't post receipts,
names or other personal details there: issues are public.
