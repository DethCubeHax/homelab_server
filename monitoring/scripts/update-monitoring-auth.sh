#!/usr/bin/env bash
# Sync MONITORING_PASSWORD from .env to Grafana. Prometheus/Loki have no login.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${ROOT}/.env"

[[ -f "${ENV_FILE}" ]] || { echo "Missing ${ENV_FILE}" >&2; exit 1; }
# shellcheck disable=SC1090
source "${ENV_FILE}"

: "${MONITORING_PASSWORD:?Set MONITORING_PASSWORD in .env}"
: "${MONITORING_DIR:?Set MONITORING_DIR in .env}"
MONITORING_ADMIN_EMAIL="${MONITORING_ADMIN_EMAIL:-you@example.com}"

cd "${ROOT}"

grafana_admin_login() {
  docker run --rm \
    -v "${MONITORING_DIR}/grafana:/data:ro" \
    alpine:3.20 \
    sh -c 'apk add --no-cache sqlite >/dev/null && sqlite3 /data/grafana.db "SELECT login FROM user WHERE is_admin=1 LIMIT 1;"'
}

echo "Stopping Grafana..."
docker compose stop grafana

echo "Resetting admin password..."
docker compose run --rm --no-deps --entrypoint grafana grafana \
  cli admin reset-admin-password "${MONITORING_PASSWORD}"

echo "Starting Grafana..."
docker compose up -d grafana

echo "Waiting for Grafana..."
for _ in $(seq 1 30); do
  curl -sf http://127.0.0.1:3000/api/health >/dev/null 2>&1 && break
  sleep 2
done

ADMIN_LOGIN="$(grafana_admin_login)"
echo "Setting admin email to ${MONITORING_ADMIN_EMAIL}..."
SESSION="$(
  curl -sf -X POST http://127.0.0.1:3000/login \
    -H 'Content-Type: application/json' \
    -d "{\"user\":\"${ADMIN_LOGIN}\",\"password\":\"${MONITORING_PASSWORD}\"}" \
    -c - | awk '/grafana_session/{print $NF}'
)"
if [[ -n "${SESSION}" ]]; then
  curl -sf -b "grafana_session=${SESSION}" \
    -H 'Content-Type: application/json' \
    -X PUT "http://127.0.0.1:3000/api/user" \
    -d "{\"email\":\"${MONITORING_ADMIN_EMAIL}\"}" >/dev/null || true
fi

echo "Done."
echo "  LAN:      http://$(hostname -I | awk '{print $1}'):3000"
echo "  Remote:   https://grafana.example.com"
echo "  Username: ${ADMIN_LOGIN}"
echo "  Password: (MONITORING_PASSWORD in .env)"
