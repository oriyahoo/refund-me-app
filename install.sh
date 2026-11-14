#!/bin/sh
# Refund-Me installer: puts docker-compose.yml, .env and the encryption key in a folder, then
# pulls the published image and starts it. Run it again at any time: it keeps your .env and your
# key, and upgrades to the version in .env.
#
#   curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/install.sh | sh
#   curl -fsSL https://raw.githubusercontent.com/oriyahoo/refund-me-app/main/install.sh | sh -s -- --postgres
#
# Options:
#   --dir <path>   where to install (default: ./refund-me)
#   --postgres     also run a bundled PostgreSQL database, with a generated admin password
#   --port <n>     the port on this server (default 3855)
#   --no-start     prepare the folder only
#
# Prefer to read it first? Download it, read it, then run `sh install.sh`.
set -eu

REPO_RAW="${REFUND_ME_RAW:-https://raw.githubusercontent.com/oriyahoo/refund-me-app/main}"
DIR="./refund-me"
POSTGRES=0
PORT=""
START=1

while [ $# -gt 0 ]; do
  case "$1" in
    --dir) DIR="$2"; shift 2 ;;
    --postgres) POSTGRES=1; shift ;;
    --port) PORT="$2"; shift 2 ;;
    --no-start) START=0; shift ;;
    -h|--help) sed -n '2,16p' "$0" 2>/dev/null || true; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

say() { printf '\033[1m%s\033[0m\n' "$*"; }
fail() { printf 'Refund-Me install: %s\n' "$*" >&2; exit 1; }

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

mkdir -p "$DIR"
cd "$DIR"
say "Installing Refund-Me in $(pwd)"

# The compose file is always refreshed (it carries no settings of yours); .env is never overwritten.
fetch "$REPO_RAW/docker-compose.yml" docker-compose.yml
fetch "$REPO_RAW/.env.example" .env.example
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env (your settings; edit it any time)."
fi
# .env can hold the bundled database's password: only its owner reads it.
chmod 600 .env
if [ -n "$PORT" ]; then
  if grep -q '^REFUND_ME_PORT=' .env; then sed -i.bak "s/^REFUND_ME_PORT=.*/REFUND_ME_PORT=$PORT/" .env && rm -f .env.bak
  else echo "REFUND_ME_PORT=$PORT" >> .env; fi
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
  if ! grep -q '^POSTGRES_ADMIN_PASSWORD=.' .env; then
    echo "POSTGRES_ADMIN_PASSWORD=$(random 24 | tr -d '/+=' | cut -c1-28)" >> .env
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

port=$(sed -n 's/^REFUND_ME_PORT=\([0-9]*\).*/\1/p' .env | tail -1)
say "Refund-Me is starting. Open http://$(hostname 2>/dev/null || echo localhost):${port:-3855} to run the setup wizard."
if [ "$POSTGRES" = "1" ]; then
  echo "Database in the wizard: PostgreSQL, host 'postgres', port 5432, 'Not encrypted', admin 'postgres', password: POSTGRES_ADMIN_PASSWORD in .env."
fi
echo "Upgrade later: run this installer again, or: cd $(pwd) && docker compose $PROFILE pull && docker compose $PROFILE up -d"
