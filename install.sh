#!/bin/sh
# Refund-Me installer: puts docker-compose.yml, .env and the encryption key in a folder, then
# pulls the published image and starts it. Run it again at any time: it keeps your .env and your
# key, and upgrades to the version in .env.
#
#   curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/install.sh | sh
#   curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/install.sh | sh -s -- --url https://expenses.company.com --cloudflare
#
# Options:
#   --dir <path>        where to install (default: ./refund-me)
#   --url <address>     the address people will use, e.g. https://expenses.company.com (APP_URL)
#   --cloudflare        people reach it through Cloudflare (its proxy or a tunnel): read the
#                       visitor's address from Cloudflare's header (CLIENT_IP_HEADER)
#   --proxy-ip <list>   the address(es) of your reverse proxy (nginx, Traefik, Coolify...),
#                       comma-separated, e.g. 172.18.0.0/16 (TRUSTED_PROXIES)
#   --postgres          also run a bundled PostgreSQL database, with a generated admin password
#   --port <n>          the port on this server (default 3855)
#   --no-prompt         don't ask questions (they're only asked in a terminal, on a first install)
#   --no-start          prepare the folder only
#
# Prefer to read it first? Download it, read it, then run `sh install.sh`.
set -eu

REPO_RAW="${REFUND_ME_RAW:-https://raw.githubusercontent.com/oriyahoo/refund-me-app/main}"
DIR="./refund-me"
POSTGRES=0
PORT=""
URL=""
CLOUDFLARE=0
PROXY_IP=""
PROMPT=1
START=1

need() { [ $# -ge 2 ] && [ -n "$2" ] || { echo "Option $1 needs a value." >&2; exit 2; }; }
while [ $# -gt 0 ]; do
  case "$1" in
    --dir) need "$@"; DIR="$2"; shift 2 ;;
    --url) need "$@"; URL="$2"; shift 2 ;;
    --cloudflare) CLOUDFLARE=1; shift ;;
    --proxy-ip) need "$@"; PROXY_IP="$2"; shift 2 ;;
    --postgres) POSTGRES=1; shift ;;
    --port) need "$@"; PORT="$2"; shift 2 ;;
    --no-prompt) PROMPT=0; shift ;;
    --no-start) START=0; shift ;;
    -h|--help) sed -n '2,23p' "$0" 2>/dev/null || echo "See https://github.com/oriyahoo/refund-me-app/blob/main/INSTALL.md"; exit 0 ;;
    *) echo "Unknown option: $1 (--help lists them)" >&2; exit 2 ;;
  esac
done

say() { printf '\033[1m%s\033[0m\n' "$*"; }
fail() { printf 'Refund-Me install: %s\n' "$*" >&2; exit 1; }

# Checked before anything is written.
valid_url() { printf '%s' "$1" | grep -Eq '^https?://[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?(:[0-9]{1,5})?/?$'; }
valid_ips() { printf '%s' "$1" | grep -Eq '^[0-9A-Fa-f.:/]+(,[0-9A-Fa-f.:/]+)*$'; }
[ -z "$URL" ] || valid_url "$URL" || fail "--url should look like https://expenses.company.com (no path)."
[ -z "$PROXY_IP" ] || valid_ips "$PROXY_IP" || fail "--proxy-ip takes addresses or ranges, comma-separated, e.g. 172.18.0.0/16"
[ -z "$PORT" ] || printf '%s' "$PORT" | grep -Eq '^[0-9]{1,5}$' || fail "--port takes a number."

# What it needs.
command -v docker >/dev/null 2>&1 || fail "Docker isn't installed. See https://docs.docker.com/engine/install/"
docker compose version >/dev/null 2>&1 || fail "Docker Compose (the 'docker compose' command) isn't available. Install the Compose plugin."
docker info >/dev/null 2>&1 || fail "Can't reach Docker. Is it running, and may this user use it? (Try with sudo, or add the user to the docker group.)"
if command -v curl >/dev/null 2>&1; then fetch() { curl -fsSL "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then fetch() { wget -qO "$2" "$1"; }
else fail "Needs curl or wget."; fi
random() { # $1 bytes, base64
  if command -v openssl >/dev/null 2>&1; then openssl rand -base64 "$1"
  else head -c "$1" /dev/urandom | base64 | tr -d '\n'; echo; fi
}

# A setting in .env: replaces "KEY=..." or the commented "# KEY=..." line, else adds it.
set_env() {
  awk -v k="$1" -v v="$2" '
    !done && ($0 ~ "^" k "=" || $0 ~ "^# " k "=") { print k "=" v; done = 1; next }
    { print }
    END { if (!done) print k "=" v }
  ' .env > .env.tmp && cat .env.tmp > .env && rm -f .env.tmp
}
is_set() { grep -q "^$1=." .env; }

mkdir -p "$DIR"
cd "$DIR"
say "Installing Refund-Me in $(pwd)"

# The compose file is always refreshed (it carries no settings of yours); .env is never overwritten.
fetch "$REPO_RAW/docker-compose.yml" docker-compose.yml
fetch "$REPO_RAW/.env.example" .env.example
FIRST=0
if [ ! -f .env ]; then
  cp .env.example .env
  FIRST=1
  echo "Created .env (your settings; edit it any time)."
fi
# .env can hold the bundled database's password: only its owner reads it.
chmod 600 .env

# A first install in a terminal: ask what the options would have said. Read from the terminal
# itself, so it works when the script comes through a pipe (curl ... | sh).
if [ "$PROMPT" = "1" ] && [ "$FIRST" = "1" ] && [ -z "$URL" ] && [ "$CLOUDFLARE" = "0" ] && [ -z "$PROXY_IP" ] \
   && [ -t 1 ] && (: </dev/tty) 2>/dev/null; then
  ask() { printf '%s' "$1" > /dev/tty; IFS= read -r REPLY < /dev/tty || REPLY=""; }
  echo
  say "Two quick questions (Enter skips; everything can be changed later in .env):"
  while :; do
    ask "1. The address people will use, e.g. https://expenses.company.com: "
    [ -z "$REPLY" ] && break
    REPLY=${REPLY%/}
    if valid_url "$REPLY"; then URL=$REPLY; break; fi
    echo "   That doesn't look like an address (https://name, no path). Try again or press Enter."
  done
  echo "2. How will people reach it?"
  echo "     1) Through Cloudflare (its proxy or a Cloudflare Tunnel)"
  echo "     2) Through another reverse proxy (nginx, Traefik, Caddy, Coolify, IIS...)"
  echo "     3) Directly on this server's port, or not sure yet"
  ask "   Choose 1, 2 or 3 [3]: "
  case "$REPLY" in
    1) CLOUDFLARE=1 ;;
    2) while :; do
         ask "   The proxy's address or range, e.g. 172.18.0.0/16 (Enter to skip): "
         [ -z "$REPLY" ] && break
         if valid_ips "$REPLY"; then PROXY_IP=$REPLY; break; fi
         echo "   Addresses or ranges only, comma-separated. Try again or press Enter."
       done ;;
  esac
  echo
fi

[ -z "$PORT" ] || set_env REFUND_ME_PORT "$PORT"
if [ -n "$URL" ]; then
  set_env APP_URL "${URL%/}"
  echo "APP_URL=${URL%/}: links in emails and sign-in use this address."
  case "$URL" in http://*) echo "Note: that address is plain http. Put HTTPS in front for real use (INSTALL.md → HTTPS)." ;; esac
fi
if [ "$CLOUDFLARE" = "1" ]; then
  set_env CLIENT_IP_HEADER "cf-connecting-ip,x-forwarded-for"
  echo "CLIENT_IP_HEADER=cf-connecting-ip,x-forwarded-for: the activity log and sign-in limits see each visitor's own address."
fi
if [ -n "$PROXY_IP" ]; then
  set_env TRUSTED_PROXIES "$PROXY_IP"
  echo "TRUSTED_PROXIES=$PROXY_IP: forwarding headers are believed only from there."
fi

# The key that encrypts the passwords the wizard saves. Created once, never replaced.
if [ ! -f refund-me-secret.txt ]; then
  (umask 077; random 32 > refund-me-secret.txt)
  echo "Created refund-me-secret.txt: the encryption key. Keep a copy in your password manager."
fi
# The app runs as user 1000 inside the container and must be able to read the key.
if [ "$(id -u)" = "0" ]; then
  chown 1000:1000 refund-me-secret.txt && chmod 600 refund-me-secret.txt
elif [ "$(id -u)" != "1000" ]; then
  chmod 644 refund-me-secret.txt
  echo "Note: refund-me-secret.txt is readable by other users of this server so the app can read it."
  echo "      For tighter access: sudo chown 1000:1000 refund-me-secret.txt && sudo chmod 600 refund-me-secret.txt"
else
  chmod 600 refund-me-secret.txt
fi

PROFILE=""
if [ "$POSTGRES" = "1" ]; then
  if ! is_set POSTGRES_ADMIN_PASSWORD; then
    set_env POSTGRES_ADMIN_PASSWORD "$(random 24 | tr -d '/+=' | cut -c1-28)"
    echo "Added a generated POSTGRES_ADMIN_PASSWORD to .env (the wizard asks for it)."
  fi
  PROFILE="--profile postgres"
fi

if [ "$START" = "0" ]; then
  say "Ready. Start it with: cd $(pwd) && docker compose $PROFILE up -d"
  exit 0
fi

# shellcheck disable=SC2086
docker compose $PROFILE pull
# shellcheck disable=SC2086
docker compose $PROFILE up -d

# Where to open the wizard: the server's IP address works whatever the host-name settings say.
port=$(sed -n 's/^REFUND_ME_PORT=\([0-9]*\).*/\1/p' .env | tail -1)
ip=$(hostname -I 2>/dev/null | awk '{print $1}')
say "Refund-Me is starting. Open http://${ip:-<this server>}:${port:-3855} to run the setup wizard."
url=$(sed -n 's/^APP_URL=//p' .env | tail -1)
[ -z "$url" ] || echo "Once your proxy points $url at this server, people use that address."
if [ "$POSTGRES" = "1" ]; then
  echo "Database in the wizard: PostgreSQL, host 'postgres', port 5432, 'Not encrypted', admin 'postgres', password: POSTGRES_ADMIN_PASSWORD in .env."
fi
echo "Upgrade later: run this installer again, or: cd $(pwd) && docker compose $PROFILE pull && docker compose $PROFILE up -d"
