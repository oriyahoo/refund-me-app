# Installing Refund-Me

Refund-Me runs on your own server as one Docker container, from the published image
`ghcr.io/oriyahoo/refund-me`. A setup wizard in the browser connects the database and file
storage, creates the first admin, and sets up sign-in, email, branding and OCR. This guide is for
the IT person doing the install. On [Coolify](https://coolify.io): see [On Coolify](#on-coolify).

- [Requirements](#requirements)
- [Quick start](#quick-start)
- [On Coolify](#on-coolify)
- [The setup wizard](#the-setup-wizard)
- [Database and least-privilege logins](#database-and-least-privilege-logins)
- [File storage](#file-storage)
- [Moving to another database or storage](#moving-to-another-database-or-storage)
- [HTTPS and the app's address](#https-and-the-apps-address)
- [Sign-in with Microsoft or Google](#sign-in-with-microsoft-or-google)
- [Reading receipts (OCR) and the optional GPU engine](#reading-receipts-ocr-and-the-optional-gpu-engine)
- [Upgrades](#upgrades)
- [Backups](#backups)
- [Configuring without the wizard](#configuring-without-the-wizard)
- [Troubleshooting](#troubleshooting)

## Requirements

- A Linux server (or VM) with Docker and Docker Compose. 2 CPU cores and 2 GB RAM are enough
  for a small office; reading a receipt takes a few seconds of CPU.
- A database: the **built-in SQLite** (one server, up to about 50 users, nothing to install) or
  one of **PostgreSQL 15+** (recommended), **SQL Server 2017+ / Azure SQL**, **MySQL 8+ /
  MariaDB 10.6+**.
- For production: a reverse proxy with HTTPS in front of the container (see below).
- Optional: an SMTP server for outgoing email; a Microsoft Entra ID or Google Workspace tenant
  for single sign-on.

The app needs **no internet access**: OCR runs locally, and PDF reports are rendered by the
Chromium inside the image.

## Quick start

```sh
curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/install.sh | sh
```

The installer makes a `refund-me` folder with `docker-compose.yml`, your settings (`.env`) and the
encryption key (`refund-me-secret.txt`), pulls the image and starts it. Open
`http://<server>:3855`: the setup wizard opens. Run in a terminal on a first install, it asks for
the address people will use and whether they come through Cloudflare or another proxy (see
[HTTPS and the app's address](#https-and-the-apps-address) for why that matters). Options:

- `--url <address>`: `APP_URL`, the address people will use.
- `--cloudflare`: `CLIENT_IP_HEADER=cf-connecting-ip,x-forwarded-for`.
- `--proxy-ip <list>`: `TRUSTED_PROXIES`, your proxy's addresses or ranges.
- `--postgres`: a bundled PostgreSQL with a generated admin password.
- `--port <n>`, `--dir <path>`, `--no-prompt`, `--no-start`.

Run it again later to upgrade; it never replaces your `.env` or your key, and options given again
update just those settings.

**By hand**, the same steps:

```sh
mkdir refund-me && cd refund-me
curl -fsSLO https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/docker-compose.yml
curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/.env.example -o .env
openssl rand -base64 32 > refund-me-secret.txt
sudo chown 1000:1000 refund-me-secret.txt && sudo chmod 600 refund-me-secret.txt
docker compose up -d
```

To change the port, set `REFUND_ME_PORT=8080` in `.env`. To run a PostgreSQL database alongside
the app (handy when there's no database server yet):

```sh
echo "POSTGRES_ADMIN_PASSWORD=$(openssl rand -base64 24)" >> .env
docker compose --profile postgres up -d
```

In the wizard choose PostgreSQL, host `postgres`, port `5432`, encryption "Not encrypted"
(traffic stays inside Docker's network), admin user `postgres` and the password from `.env`.

### The encryption key

Passwords the wizard saves (database logins, SMTP, SSO secrets) are encrypted with the key in
`refund-me-secret.txt`, which Docker hands to the app as a secret. It lives outside the data
volume, so a copy of the volume alone reveals nothing. The app runs as user 1000 inside the
container, so that user must be able to read the file (the installer sets this up).

**Keep a copy of the key in your password manager.** Without it the saved settings can't be read
and the wizard would have to be run again. Never change it on an existing install.

## On Coolify

1. **Projects → your project → + New → Docker Compose Empty**, and paste
   [`docker-compose.yml`](docker-compose.yml).
2. Coolify has no secret files: delete the `secrets:` lines (under `app` and at the end) and the
   `REFUND_ME_SECRET_FILE` line, and add an environment variable `REFUND_ME_SECRET` with the
   output of `openssl rand -base64 32` (mark it as a secret, and keep a copy in your password
   manager).
3. Enter the address people will use in the app's **Domains** field, then **Deploy**.
4. To upgrade: **Redeploy** (with `REFUND_ME_VERSION` set to a version, change it first).

## The setup wizard

The first visit opens the wizard directly: whoever reaches a fresh install first sets it up, so
finish it right after starting the container. To protect that window (for example when the
server is reachable from the internet), set `SETUP_CODE` to a code of your choice: the wizard
then asks for it first. It isn't needed once the first admin exists.

1. **Database**: the built-in SQLite, or a server (see the next section).
2. **File storage**: this server (the data volume), S3-compatible storage or Azure Blob Storage.
   A test file is written, read back and deleted before continuing.
3. **First admin**: company name, default language, and the admin's name, email and password.
   The admin is signed in and the address the browser used is saved as the app's address.
4. **Sign-in (SSO)**: Microsoft Entra ID and/or Google (optional).
5. **Email**: the SMTP server, with a "send a test to me" button (optional; without it emails
   are written to the log). Ports 25, 465, 587, 2525 or 1025. A failed test says what kind of
   failure it was; the server's full answer is in the server log. The saved password is reused
   only for the same server, port, user and encryption: change any of them and type it again.
6. **Branding**: logo, color, currency and language. An SVG logo is saved as the PNG it draws.
7. **OCR engine**: "Test on a sample receipt" checks that receipt reading works on this server.

Steps 4–7 can be skipped and changed later under **Admin → Sign-in** and **Admin → System**.

## Database and least-privilege logins

For a database server, the wizard creates three things and nothing else:

| | Rights | Used for |
|---|---|---|
| database `expenses` (name is yours) | UTF-8 (`utf8mb4` on MySQL) | the app's tables |
| login `expenses_owner` | owns the schema in that database only | migrations, at install and at each start |
| login `expenses_app` | `SELECT, INSERT, UPDATE, DELETE` on that database only: no DDL, no DROP, no server rights | everything the running app does |

Both logins get generated 32-character passwords, stored encrypted. The wizard checks that the
app login can read and write but **can't** create tables, and refuses to continue otherwise.

There are two ways to do it:

- **With an admin login (used once, never stored)**: the wizard checks the server version, TLS,
  and that the login can create databases and logins, then does everything itself. If a step
  fails, whatever it created is dropped again so you can simply retry. Admin rights needed:
  PostgreSQL `CREATEDB` + `CREATEROLE` (or superuser; on PostgreSQL 16+ the wizard also grants
  itself membership in the owner role, which `CREATEROLE` allows); MySQL `CREATE`,
  `CREATE USER` and `GRANT OPTION`; SQL Server `CREATE ANY DATABASE` + `ALTER ANY LOGIN`.
- **"I'll run the script myself"**: the wizard generates the SQL with fresh passwords and fills
  the two logins in. Review and run the script with `psql`, `mysql`, `sqlcmd` or SSMS, then
  press "Connect & continue": the wizard migrates as the owner and checks the app login.

Encryption choices: **verify** (TLS with a certificate the container trusts: public CA, or add
your CA to the image), **self-signed** (TLS without certificate checks; PostgreSQL and SQL
Server only) or **not encrypted** (only inside a trusted network or Docker's own network).

Notes per database:

- **PostgreSQL**: version 15 or newer. The app login gets `CONNECT`, `USAGE` on schema `public`
  and row rights on the owner's tables, including tables added by future migrations (default
  privileges).
- **SQL Server**: the owner is `db_owner` of the app's database; the app login is in
  `db_datareader` and `db_datawriter`. The wizard and the script turn on
  `READ_COMMITTED_SNAPSHOT` for the database, so reads don't wait behind other people's saves
  (SQL Server's default makes them queue, and makes deadlocks likely). On a database set up
  before 14 Nov 2026, turn it on once, with the app stopped:
  `ALTER DATABASE [expenses] SET READ_COMMITTED_SNAPSHOT ON WITH ROLLBACK IMMEDIATE;` (the app
  logs a warning at start while it is off). **Azure SQL Database** works with the wizard (it creates
  the database with the server's default service tier; create it yourself first in the portal if
  you want a specific tier, and use the script option). Azure SQL Database doesn't support `USE`:
  run the script's first part connected to `master` and the part after `USE` connected to the
  app's database.
- **MySQL / MariaDB**: grants are on the app's database (`expenses.*`), which covers future
  tables. The "self-signed" option isn't available: use a trusted certificate, or no encryption
  inside a trusted network.

## File storage

| Option | Use | Notes |
|---|---|---|
| This server | small installs | files in the data volume (`/data/files`); back it up |
| Cloudflare R2 | off-server storage, no download fees | a private bucket and an R2 API token with **Object Read & Write** on that bucket only; the account ID is on the R2 overview page. EU-jurisdiction buckets: choose the EU location |
| S3-compatible | AWS S3, MinIO, Wasabi | a private bucket; the key needs `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` on it. For MinIO tick "bucket in the path" |
| Azure Blob Storage | Azure | a private container and a container **SAS token** with read, write, delete (and **list**, for moving to another storage later); renew it before it expires |

The files can be moved to another storage later: see the next section.

Addresses typed into the app (storage, database server, mail server, AI server) can be anywhere
on your network or the internet, except cloud metadata and link-local addresses
(169.254.0.0/16, fe80::/10, Azure's 168.63.129.16, 0.0.0.0): names are looked up, and checked
again before each request, and storage and AI requests don't follow redirects.

## Moving to another database or storage

**Admin → System** can move a running install, with no manual export:

- **Move to another database**: the same choices as the wizard (a new SQLite file, or
  PostgreSQL, SQL Server, MySQL/MariaDB with an admin login or with the two logins IT created
  from the script). The new database must be empty. The app creates and migrates it, then:
  1. checks that every text value fits the new database's columns (MySQL keeps short text to
     191 characters, SQL Server to 255; PostgreSQL and SQLite have no such limit). A value that
     doesn't fit stops the move here, naming the table and column, before anything pauses;
  2. pauses saving, waits for saves already running to finish, and copies every row (ids,
     dates and sign-in sessions unchanged, so nobody is signed out);
  3. checks the copy: the row counts, and every table's ids and dates read back from the new
     database;
  4. switches, and saving goes on against the new database.

  **Saving is paused for the whole copy.** It takes about 2 minutes per million rows on one
  machine (measured SQLite to SQLite), longer to a database server over the network. A small
  office has a few hundred thousand rows; a company of 5,000 people after a few years has tens
  of millions (most of them activity log entries), so the pause can be an hour or more: move at
  a quiet time, or shorten the activity log's retention first. Reading works as usual. A save
  that waits more than a minute fails with a message that the data is being moved, and can be
  done again afterwards; nothing already saved is lost. If anything fails, saving goes on at
  once against the current database, and the new one is emptied again in the background.
- **Move files to another storage**: test the new storage, then every receipt, logo, profile
  photo, problem-report screenshot and activity log archived before a data reset is copied
  under the same name and the app switches. Files uploaded during the copy are copied too.
  Receipt previews aren't copied: they're made again the first time they're opened. The
  screenshots and archives are found by listing the old storage (Azure: the SAS needs the list
  permission); a folder that can't be listed is named in the server log and left behind.

The old database and the old files are **not** deleted: keep them as a backup until you're sure,
then remove them yourself. An audit-log entry records each move.

If the database or storage is set by environment variables, the move still works: the app uses
the new place while the variables still name the old one, and Admin → System shows a reminder.
Update the variables (`DATABASE_*`, `STORAGE_*`) to the new place when convenient; once they
change, they win again.

## HTTPS and the app's address

Put the container behind your reverse proxy (nginx, Traefik, Caddy, IIS/ARR, an Azure
Application Gateway…) with HTTPS, forwarding to port 3855. Allow request bodies of at least
**20 MB** (receipt uploads; nginx: `client_max_body_size 20m;`).

The app's address is used in emailed links and SSO redirects. The wizard saves the address
the browser used during setup; change it under **Admin → System**, or fix it with `APP_URL`.
If you open the wizard through a different address than people will use, correct it there.

Sign-in cookies are marked `Secure` whenever the browser came over HTTPS (the proxy's
`X-Forwarded-Proto: https`), so they're never sent over plain HTTP to that address; over a
plain-HTTP address they can't be. On a plain-HTTP address such as `http://<server>:3855`, the
browser also sends the session cookie to every other service on that server (cookies aren't
kept apart by port). Prefer a name of its own with HTTPS for office use too.

**The client's address behind a proxy.** Sign-in is limited per client address as well as per
account. The app sees only what the proxy writes, so tell it which header that is:

- `CLIENT_IP_HEADER`: the header the proxy sets, replacing anything the client sent. Behind
  Cloudflare (a tunnel or the proxy): `cf-connecting-ip`. Default `x-forwarded-for`.
- `TRUSTED_PROXIES`: the proxies' own addresses or ranges, comma-separated
  (`10.0.1.5,172.18.0.0/16`). With them, an `X-Forwarded-For` chain is read from the right,
  skipping those proxies. Without them, a chain of two or more addresses (two proxies) names
  no client, and those clients share one limit.

On a port reached directly, without a proxy, a client can write these headers itself. With
`TRUSTED_PROXIES` set, the image stops that: forwarding headers (the address, `X-Forwarded-Proto`,
the `CLIENT_IP_HEADER` names) are removed from every connection that doesn't come from one of the
listed proxies, before the app sees them, so the address is the real connection's and "HTTPS"
can't be claimed over plain HTTP. List the proxies exactly (behind Coolify, its proxy's Docker
network, e.g. `10.0.0.0/8`; check the address in the activity log afterwards): a proxy left out
loses its headers too, its visitors show its address, and the AI-assistant server (HTTPS only)
refuses what comes through it. Without `TRUSTED_PROXIES` the per-address
limits on such a port are only a brake, and the addresses in the activity log are as the client
reported them. The per-account limits hold whatever the address:
10 wrong passwords from one place in 15 minutes pause that place; 50 from everywhere pause the
account except on the browsers its owner signed in from before, and email the owner. Email
links and Microsoft/Google sign-in aren't paused.

## Sign-in with Microsoft or Google

**Microsoft Entra ID**: in the Azure portal, *App registrations → New registration*. Supported
account types: *this organizational directory only*. Redirect URI (platform **Web**):
`https://<your address>/api/auth/callback/microsoft`. Then *Certificates & secrets → New client
secret*. In the wizard enter the Application (client) ID, the Directory (tenant) ID and the
secret value. Note the secret's expiry date.

**Google**: in Google Cloud Console, *APIs & Services → Credentials → Create credentials → OAuth
client ID*, type *Web application*, authorized redirect URI
`https://<your address>/api/auth/callback/google`. For Workspace, set the consent screen to
*Internal*.

Only people an admin added can sign in, whatever the method; SSO accounts are matched by email.
Once SSO works, the admin can turn email links and passwords off (**Admin → Sign-in**); admins
can always still sign in with a password, so a broken SSO setup can't lock everyone out.

## Reading receipts (OCR) and the optional GPU engine

Every install reads receipts on the **CPU** (Tesseract, Hebrew and English, inside the
container). Photos are first cropped to the paper and straightened; blurry photos get a "retake?"
warning. Digital PDF invoices are read from their text directly. `OCR_WORKERS` sets how many
receipts are read at once (default: one per two CPU cores, up to 4; at most 16; about 100 MB of
memory each).

- **Taking turns.** Receipts are read oldest first, but someone with a receipt already being read
  waits while anyone else's is due, so one person's 300 pages don't hold up everyone else.
  Reminder emails have their own queue and never wait behind receipts.
- **Uploaded files are opened in worker threads, with a time limit.** PDFs, iPhone (HEIC) photos
  and the photo clean-up run outside the web server's own thread, so a slow or crafted file can't
  stall the app. A file that takes longer than `FILE_WORKER_TIMEOUT_MS` (default 30000) is
  stopped and treated as unreadable: refused at upload, or marked unreadable for the employee to
  type in. `FILE_WORKERS` sets how many such files are opened at once (default 2; each up to
  about 512 MB while busy).
- **More reading capacity.** On a busy install (thousands of people, everyone uploading on the
  due date), run the background work in a second container from the same image, with the same
  settings and database (PostgreSQL, SQL Server or MySQL; the same file storage), not published
  on any port, and give it the CPUs and a larger `OCR_WORKERS`. Set `JOB_RUNNER=off` on the
  container people use, so it only serves the app.
- **A receipt that can't be read** after three tries (the file storage was unreachable, say) is
  marked unreadable, so the employee types it in or presses "Read again"; it never stays
  "reading…". A tidy-up every few hours does the same for receipts left waiting with no reading
  queued (e.g. from before an upgrade).
- **Receipts in another currency.** When the AI tier names a currency other than the company's
  (or the text clearly does, with no shekel sign and no Israeli business ID), the amount is left
  for the employee to enter in the company's currency, and the receipt's own currency and total
  are shown to them, to the reviewers and in the exports. Nothing is converted.
- **Raw OCR text** (everything printed on the receipt) is kept `OCR_TEXT_KEEP_DAYS` days (default
  30; 0: not kept), only to look into a misreading. The receipt file and the expense's values are
  kept regardless.
- **Addresses in the activity log.** Each entry made while someone used the app keeps the address
  it came from (shown in the activity log, its export and the assistants' `activity_log`) for
  `ACTIVITY_IP_KEEP_DAYS` days (default 365; 0: not kept). After that the entry stays and only
  its address is cleared.

A **GPU engine** is optional and reads difficult photos better: a vision AI model served by
[Ollama](https://ollama.com) or [vLLM](https://docs.vllm.ai) on a machine with a GPU in your
network. The app sends it the photo, and the CPU engine's rules check its answer (business ID
check digit, VAT that matches 17%/18% of the total, a plausible date). If the GPU server is down
or slow, receipts are read on the CPU as usual.

On the same Docker host with an NVIDIA GPU and the
[NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/):

```sh
docker compose --profile gpu up -d
docker compose exec ollama ollama pull qwen2.5vl:7b    # about 6 GB; 8 GB+ of GPU memory
```

Then **Admin → System → GPU engine**: address `http://ollama:11434`, model `qwen2.5vl:7b`,
and "Test the GPU engine on the sample". On a separate GPU server, run Ollama or vLLM there and
enter its address (vLLM: `http://<server>:8000`, plus an API key if you set one). Which model
reads Hebrew receipts best is still to be measured with real receipts; any vision model the
server offers can be entered.

### Cloud AI (optional)

For photos the CPU engine can't read (faded thermal paper, condensed dot-matrix print) without
running a GPU server, an admin can turn on **cloud AI**: **Admin → System → Cloud AI** (or the
wizard's OCR step).

1. Pick a **provider**: Claude (Anthropic), OpenAI, Grok (xAI), OpenRouter, or any other
   OpenAI-compatible service (enter its address, e.g. Azure OpenAI, Google Gemini's
   OpenAI-compatible endpoint, a company AI gateway).
2. Enter that provider's **API key** (stored encrypted).
3. Type any **model** that accepts images, or press **Load models** to pick from the
   provider's current list (OpenRouter's list is filtered to models that accept images).
4. **Test on the sample receipt**: sends only the bundled synthetic sample.
5. Confirm that receipt photos may be sent to the provider, and turn it on.

Claude runs through Anthropic's own API (Opus 5.5 by default: about $0.02 per receipt; Haiku
5.5: about $0.0003); the others through the OpenAI chat API. Check each provider's pricing.

It's off by default and stays off until an admin turns it on. When on, **every uploaded
receipt photo is sent to that provider** (with OpenRouter, on to the company running the chosen
model). Receipts can include names, the last card digits and car plates, so under Israel's
Privacy Protection Law this needs a data-processing agreement and a line in your privacy
notice; check each provider's data-retention terms. Every answer is checked by the same receipt
rules, and the CPU engine's reading is used if the service is down, declines, or answers
something that fails the checks. A local GPU engine, if configured, is used instead of the
cloud. Environment alternative: `OCR_CLOUD_PROVIDER`, `OCR_CLOUD_API_KEY`, `OCR_CLOUD_MODEL`,
`OCR_CLOUD_BASE_URL`.

## Upgrades

```sh
docker compose pull
docker compose up -d
```

(or run the installer again). With `REFUND_ME_VERSION` set to a version in `.env`, change it to
the new one first. What each version brings: [CHANGELOG.md](CHANGELOG.md).

On every start the container applies any new database migrations as the **owner** login, then
runs the app as the **app** login. If a migration fails, the container stops with the reason in
`docker compose logs app` instead of serving a half-upgraded app. Take a backup first.

A migration is never stopped half-way: one that builds an index on a big table can take minutes,
and the log says every minute that it's still running (and louder after
`MIGRATE_TIMEOUT_MINUTES`). **Don't stop or redeploy the container while it migrates**: a
migration cut short has to be repaired by hand (below).

If your change process requires DBAs to run migrations themselves, set `AUTO_MIGRATE=off` and
run them from the image:

```sh
docker compose run --rm --entrypoint sh app -c \
  'cd /app/migrate && DATABASE_PROVIDER=postgresql DATABASE_MIGRATE_URL="postgresql://expenses_owner:…@db:5432/expenses" node node_modules/prisma/build/index.js migrate deploy'
```

### If an upgrade fails

The log ends with the migration's name (e.g. `20261113235650_wave1_receipt_indexes`), the
database's error and what to do. Prisma marks a failed migration and refuses every later start
(error `P3009`) until it's resolved, so restarting alone doesn't help. What the app does first,
by database:

- **SQLite**: when there's a migration to apply, the app copies the database file
  (`refund-me.db.before-migrate`, next to it) and puts it back if the migration fails, so
  nothing is half-applied. Fix the cause (often a full disk: the copy needs as much free space
  as the database) and restart.
- **PostgreSQL**: the database undoes a failed migration completely. The app marks it as rolled
  back and tries once more; if it fails again, fix the cause shown and restart.
- **SQL Server**: the same, for migrations wrapped in a transaction (the ones Prisma made). A
  few hand-written data migrations aren't: their statements are safe to run again, so mark the
  migration as below and restart.
- **MySQL/MariaDB**: MySQL keeps the statements that ran before the failure (it can't undo
  table changes). Restore the backup taken before the upgrade, or compare the database with
  `prisma/mysql/migrations/<name>/migration.sql` and undo (or finish) what was applied.

Then, to mark the migration as rolled back so the next start applies it again, set
`MIGRATE_RESOLVE_ROLLED_BACK=<the migration's name>` in the app's environment (Coolify:
**Environment Variables**) and restart. Remove the variable once the app is up. The same from a
shell, with the app stopped:

```sh
docker compose run --rm --entrypoint sh app -c \
  'cd /app/migrate && DATABASE_PROVIDER=<provider> DATABASE_MIGRATE_URL="<owner URL>" node node_modules/prisma/build/index.js migrate resolve --rolled-back <name>'
```

## Backups

Back up together, at the same time:

- the **database** (your usual tool: `pg_dump`, SQL Server backups, `mysqldump`; for SQLite,
  the file `/data/refund-me.db`, e.g. `sqlite3 refund-me.db ".backup backup.db"`);
- the **files** (the `/data/files` folder, or your bucket/container's own versioning);
- the **settings**: `/data/config.json` and the key (`/data/secret.key`, or your
  `REFUND_ME_SECRET` file).

The simplest complete backup of a SQLite install is a copy of the whole data volume while the
container is stopped.

### Configuration backup

**Admin → System → Configuration backup** saves the configuration to one file, and loads it back.
The file holds:
- company details and branding (logos included);
- policies;
- sign-in (local accounts, Microsoft, Google);
- outgoing email;
- receipt reading (GPU server, cloud AI);
- AI assistant (MCP) settings;
- the app's address;
- departments;
- expense types;
- people and reporting lines;
- the database and storage connections.

It doesn't hold receipts, expenses or the activity log: those come from the database and file
backups above.

- **Download:** choose the sections. With passwords and keys included (the mail password, sign-in
  app secrets, AI keys, database and storage logins), the file is encrypted with a passphrase you
  type. Keep the passphrase apart from the file: without it the file can't be read, and the app
  doesn't keep it. Without passwords and keys, the file is plain JSON you can read and compare.
- **Load:** the app first shows, section by section, what would change. Only the sections you tick
  change, all together or not at all, and a restore point of the settings before is saved first.
- **What an import never does:**
  - It never removes anyone: people missing from the file stay as they are.
  - It never deletes an expense type: a type missing from the file is switched off.
  - The admin loading the file keeps their own role and access.
- **Restore points:** the app saves one before every load, and every hour when the settings changed
  (when only people changed, at most once a day). Kept by kind: the last 30 hourly ones for up to
  30 days, and the last 10 made before a load and the last 10 saved by hand for up to 90 days.
  They are encrypted with the app's key (`REFUND_ME_SECRET`) and stored in file storage
  (`config-backups/`); passwords and keys set by the server's environment aren't copied into
  them. Each can be compared, restored the same way, downloaded as a file, or deleted. A restore
  point is read only if it is the app's own encrypted file with the content it was saved with.
  "Reset data" deletes them all.
- **In the setup wizard:** a new install can start from the file ("Restoring from a configuration
  backup?" on the first step):
  - The database and storage steps can use the backup's connections, under the same rules as
    those steps: a database server's address, database name and options are checked and the
    connection is built again (anything else in it is refused); SQLite is the wizard's own file;
    local storage is the data folder's. The storage step comes after the database step.
  - The first admin is created as usual, then the ticked sections are applied to the new company.
  - If the chosen database already holds the company (restored from a database backup), setup
    ends there, and only the settings file's sections are applied: sign-in, email, receipt
    reading and the address.
- **Where nothing changes:** settings fixed by environment variables are never changed by a load.
  The database and storage connections aren't changed by a load in the app either: use "Move to
  another…" on the System page for that.

## Configuring without the wizard

Every setting can also come from environment variables (or Docker secrets via
`<NAME>_FILE`, e.g. `DATABASE_URL_FILE=/run/secrets/db_url`). Environment variables win over
what the wizard saved, and the wizard shows those settings as read-only. The common ones are in
[`.env.example`](.env.example) and already passed on by `docker-compose.yml`; for any other, add
it under the app's `environment:` there (e.g. `SMTP_HOST: ${SMTP_HOST:-}`) and set it in `.env`.
The main ones:

| Variable | Meaning |
|---|---|
| `DATABASE_PROVIDER`, `DATABASE_URL` | the database and the app login (skips wizard step 1) |
| `DATABASE_MIGRATE_URL` | the owner login, for migrations (default: `DATABASE_URL`) |
| `DATABASE_POOL_SIZE` | database connections per app process (default `20`; the drivers' own default is 10). Keep it under what the database allows for the app login, times the number of app instances |
| `DATABASE_STATEMENT_TIMEOUT_SECONDS` | how long one database statement may run before the database stops it (default `120`; `0`: no limit). PostgreSQL and SQL Server (whose driver otherwise stops one after 15 seconds); not MySQL |
| `ACTIVITY_IP_KEEP_DAYS` | days an activity entry keeps the address it came from (default `365`; `0`: not kept) |
| `OCR_WORKERS`, `FILE_WORKERS`, `JOB_RUNNER` | receipts read at once, PDF/HEIC files opened at once, `off` for no background work in this container (see "More reading capacity") |
| `RECEIPT_MAX_AGE_DAYS` | how old a receipt can be and still be claimed, in days (default `365`). An older date, or one in the future, is refused when the expense is saved |
| `MIGRATE_TIMEOUT_MINUTES` | after how long a migration at start is reported in the log as slow (default `30`). It is never stopped: see "If an upgrade fails" |
| `MIGRATE_RESOLVE_ROLLED_BACK` | the name of a failed migration to mark as rolled back at start, so it's applied again (see "If an upgrade fails"); remove it once the app is up |
| `STORAGE_DRIVER` | `local`, `s3`, `r2` or `azure`, with `S3_*`, `R2_*` or `AZURE_*` (skips step 2) |
| `APP_URL` | the public address |
| `TRUSTED_ORIGINS` | more addresses for the same server, comma-separated (sign-in already accepts the address the browser used, unless a proxy changes the `Host` header) |
| `ALLOWED_HOSTS` | more names the server answers to, comma-separated (a leading dot allows every name under it, e.g. `.office.local`). The app answers only under its own address, `TRUSTED_ORIGINS`, these, `localhost` and IP addresses; any other name gets 421, so a page on a name someone pointed at the server can't reach it through a staff browser (DNS rebinding). Not enforced while the app's address is still `localhost` |
| `CLIENT_IP_HEADER`, `TRUSTED_PROXIES` | which header names the client behind your proxy (e.g. `cf-connecting-ip`), and the proxies' addresses; see "HTTPS and the app's address" |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURE`, `SMTP_TLS`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | outgoing email (`SMTP_TLS=off`: an internal relay without encryption; `trust`: accept any certificate) |
| `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID` | Entra ID sign-in |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google sign-in |
| `REFUND_ME_SECRET` | the key that encrypts saved settings and signs sessions. Set it on new installs (from a secret store, or `REFUND_ME_SECRET_FILE`): without it the key is `data/secret.key`, on the same volume as the settings, so a backup of the volume holds every saved secret. Don't change it on an existing install: the saved settings would no longer decrypt |
| `SETUP_CODE` | optional: the wizard asks for this code before anything else |
| `RECOVERY_ADMIN_EMAIL` | recovery when nobody can manage the app: this person becomes an active admin when the app starts, once per value (see Troubleshooting). Remove it once used |
| `AUTO_MIGRATE=off` | don't migrate on start |
| `SMTP_RATE_PER_MINUTE` | at most this many emails a minute, for providers that limit it (Microsoft 365: 30); unset: no limit |
| `APP_TIMEZONE`, `REMINDER_HOUR` | automatic reminders (Settings → Policies) are sent from this hour in this time zone (default `Asia/Jerusalem`, `9`) |
| `DATA_DIR` | the data folder (default `/data` in the image) |

## Troubleshooting

- **The wizard asks for a setup code**: `SETUP_CODE` is set on the server; enter that value.
- **The only admin left, and nobody can sign in to their account**: the app never lets the last
  active admin be switched off, and accountants can't make admins. While a company has one active
  admin, the admin pages say so and that admin gets a weekly reminder: add a second admin before
  it's needed. If it's too late:
  1. Set `RECOVERY_ADMIN_EMAIL=new.admin@company.co.il` in the server's environment (Coolify:
     the app's Environment Variables) and restart or redeploy.
  2. On start, that person becomes an active admin: promoted if they're already in the app, added
     if not. They're emailed to sign in (with Microsoft/Google, or a sign-in link they ask for on
     the sign-in page; admins get links even with local accounts off).
  3. It's in the activity log ("made an admin from the server"), and every other active admin is
     emailed.
  4. Remove the variable. A restart with the same value does nothing again; a different address
     is handled once more.

  Whoever can change the server's environment already holds the database and the keys, so the
  setting gives them nothing new. Demo addresses (`@demo.invalid`) are refused.
- **"Can't decrypt a setting in config.json: the key changed"**: the container started with a
  different `REFUND_ME_SECRET` (or without the secret file) than the one used during setup.
  Restore the original key.
- **SSO says the redirect URI doesn't match**: the app's address (Admin → System) must be
  exactly the address people use, including `https://` and no trailing slash.
- **Sign-in links in emails point to the wrong place**: same as above.
- **Health check**: `GET /api/health` returns `{"status":"ok"}` while the app answers,
  `{"status":"setup"}` before the wizard, and 503 when the database has been unreachable for about
  two minutes. A busy moment, with every database connection in use, still answers `ok` (with
  `"database":"slow"`): Docker and the proxy shouldn't take the app out when it's busiest.
  `GET /api/health?deep=1` is the strict one for monitoring: it asks the database every time and
  answers 503 unless it replied within 4 seconds.
  Point your monitoring (Zabbix, Uptime Kuma, ...) at it, and watch the container's memory
  against `REFUND_ME_MEMORY_LIMIT`.
