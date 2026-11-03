#!/usr/bin/env bash
# Genera .env (secretos aleatorios + defaults) y levanta Compose.
# No imprime contraseñas. No sube .env al repo.
#
#   ./scripts/up.sh
#   ./scripts/up.sh --fresh-env
#   ./scripts/up.sh --detach
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FRESH=0
DETACH=()

usage() {
  cat <<'EOF'
Uso: ./scripts/up.sh [--fresh-env] [--detach]

  --fresh-env  Reescribe .env con secretos nuevos (si ya existe un volumen
               de Postgres, las claves no coinciden: docker compose down -v).
  --detach     docker compose up --build -d

Si no hay .env, lo crea. Secretos aleatorios: POSTGRES_PASSWORD,
APP_DB_PASSWORD, MIGRATION_DB_PASSWORD, JWT_SECRET, GRAFANA_ADMIN_PASSWORD.
El resto usa defaults (.env.example). Puertos ocupados pasan al secundario.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fresh-env) FRESH=1 ;;
    --detach|-d) DETACH=(-d) ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Opción desconocida: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

rand_hex() {
  local bytes="$1"
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex "$bytes"
  else
    python3 -c "import secrets; print(secrets.token_hex(${bytes}))"
  fi
}

port_in_use() {
  python3 - "$1" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket()
sock.settimeout(0.3)
try:
    sock.connect(("127.0.0.1", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
raise SystemExit(0)
PY
}

write_env() {
  local pg_pass app_pass mig_pass jwt gf_pass
  local frontend backend grafana postgres_host
  local cors api_url

  pg_pass="$(rand_hex 16)"
  app_pass="$(rand_hex 16)"
  mig_pass="$(rand_hex 16)"
  jwt="$(rand_hex 32)"
  gf_pass="$(rand_hex 16)"

  frontend=3000
  backend=8000
  grafana=3001
  postgres_host=5433
  if port_in_use 3000; then frontend=3100; fi
  if port_in_use 8000; then backend=8010; fi
  if port_in_use 3001; then grafana=3011; fi
  if port_in_use 5433; then postgres_host=5434; fi

  cors="http://localhost:${frontend}"
  api_url="http://localhost:${backend}"

  umask 077
  cat > "${ROOT}/.env" <<EOF
POSTGRES_DB=mlsre
POSTGRES_PASSWORD=${pg_pass}
APP_DB_USER=mlsre_app
APP_DB_PASSWORD=${app_pass}
MIGRATION_DB_USER=mlsre_migrate
MIGRATION_DB_PASSWORD=${mig_pass}
DATABASE_URL=postgresql+psycopg://mlsre_app:${app_pass}@db:5432/mlsre
MIGRATION_DATABASE_URL=postgresql+psycopg://mlsre_migrate:${mig_pass}@db:5432/mlsre
JWT_SECRET=${jwt}
FRONTEND_PORT=${frontend}
BACKEND_PORT=${backend}
GRAFANA_PORT=${grafana}
POSTGRES_HOST_PORT=${postgres_host}
CORS_ORIGINS=${cors}
NEXT_PUBLIC_API_URL=${api_url}
PRODUCT_IMAGES_DIR=var/product-images
PROFILE_IMAGES_DIR=var/profile-images
LOG_FILE=var/logs/app.log
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${gf_pass}
DEMO_PASSWORD=mlsre-demo
EOF
}

if [[ ! -f "${ROOT}/.env" ]]; then
  write_env
  echo "Creé .env con secretos aleatorios y defaults. No lo subas al repo."
elif [[ "${FRESH}" -eq 1 ]]; then
  write_env
  echo "Reescribí .env. Si Postgres ya tenía volumen, corré: docker compose down -v"
else
  echo "Reuso .env existente. Pasá --fresh-env para regenerar secretos."
fi

echo "Levantando con docker compose up --build ${DETACH[*]-}"
exec docker compose up --build "${DETACH[@]}"
