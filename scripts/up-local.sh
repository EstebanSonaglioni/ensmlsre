#!/usr/bin/env bash
# Levanta API + frontend en el host (sin Docker). Default: SQLite.
# Grafana/Loki siguen siendo solo Compose.
#
#   ./scripts/up-local.sh
#   ./scripts/up-local.sh --api-only
#   USE_POSTGRES=1 ./scripts/up-local.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

API_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --api-only) API_ONLY=1 ;;
    -h|--help)
      cat <<'EOF'
Uso: ./scripts/up-local.sh [--api-only]

  Sin Docker. SQLite en backend/var/mlsre.db (salvo USE_POSTGRES=1).
  Crea backend/.venv con --without-pip y get-pip (PEP 668 / HR).
  No pisa el .env de Compose: solo exporta variables al proceso.

  --api-only  No arranca Next (si Node es viejo o no está).
EOF
      exit 0
      ;;
    *)
      echo "Opción desconocida: $arg" >&2
      exit 1
      ;;
  esac
done

if [[ -f "${ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/.env"
  set +a
fi

export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:3000}"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
export PRODUCT_IMAGES_DIR="${PRODUCT_IMAGES_DIR:-var/product-images}"
export PROFILE_IMAGES_DIR="${PROFILE_IMAGES_DIR:-var/profile-images}"
export LOG_FILE="${LOG_FILE:-var/logs/app.log}"
export DEMO_PASSWORD="${DEMO_PASSWORD:-mlsre-demo}"
export FRONTEND_PORT="${FRONTEND_PORT:-3000}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"

if [[ -z "${JWT_SECRET:-}" || ${#JWT_SECRET} -lt 32 ]]; then
  if command -v openssl >/dev/null 2>&1; then
    JWT_SECRET="$(openssl rand -hex 32)"
  else
    JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  fi
  export JWT_SECRET
  echo "JWT_SECRET temporal (no estaba en .env o era corto)."
fi

if [[ "${USE_POSTGRES:-0}" != "1" ]]; then
  DB_FILE="${ROOT}/backend/var/mlsre.db"
  export DATABASE_URL="sqlite:///${DB_FILE}"
  export MIGRATION_DATABASE_URL="${DATABASE_URL}"
fi

mkdir -p "${ROOT}/backend/var/product-images" \
  "${ROOT}/backend/var/profile-images" \
  "${ROOT}/backend/var/logs"

VENV="${ROOT}/backend/.venv"
PY="${VENV}/bin/python"
if [[ ! -x "${PY}" ]]; then
  python3 -m venv --without-pip "${VENV}"
fi
if [[ ! -x "${VENV}/bin/pip" ]] && ! "${PY}" -m pip --version >/dev/null 2>&1; then
  if command -v curl >/dev/null 2>&1; then
    curl -sS https://bootstrap.pypa.io/get-pip.py | "${PY}"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://bootstrap.pypa.io/get-pip.py | "${PY}"
  else
    echo "Hace falta curl o wget para get-pip.py" >&2
    exit 1
  fi
fi

if ! "${PY}" -m pip install -r "${ROOT}/backend/requirements.txt"; then
  echo "Retry sin psycopg (modo SQLite)."
  FILTERED="$(mktemp)"
  grep -v '^psycopg' "${ROOT}/backend/requirements.txt" > "${FILTERED}"
  "${PY}" -m pip install -r "${FILTERED}"
  rm -f "${FILTERED}"
fi

cd "${ROOT}/backend"
if [[ "${USE_POSTGRES:-0}" == "1" ]]; then
  "${PY}" -m alembic upgrade head
else
  "${PY}" -m app.bootstrap
fi
"${PY}" -m app.seed

API_PID=""
FE_PID=""
cleanup() {
  if [[ -n "${FE_PID}" ]] && kill -0 "${FE_PID}" 2>/dev/null; then
    kill "${FE_PID}" 2>/dev/null || true
  fi
  if [[ -n "${API_PID}" ]] && kill -0 "${API_PID}" 2>/dev/null; then
    kill "${API_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "API en http://localhost:${BACKEND_PORT}  (demo: boss@mail.com / ${DEMO_PASSWORD})"
"${PY}" -m uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" --reload &
API_PID=$!

if [[ "${API_ONLY}" -eq 0 ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm no está; API sola. Instalá Node o usá --api-only."
  else
    cd "${ROOT}/frontend"
    npm install
    echo "UI en http://localhost:${FRONTEND_PORT}"
    npm run dev -- --hostname 0.0.0.0 --port "${FRONTEND_PORT}" &
    FE_PID=$!
  fi
fi

wait "${API_PID}"
