#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# deploy.sh — Kód feltöltése és újraindítás
# Minden update után futtatható: bash deploy/deploy.sh
#
# Előfeltétel: setup-lxc.sh már lefutott egyszer
# ─────────────────────────────────────────────────────────────

set -euo pipefail

LXC_HOST="192.168.1.26"
LXC_USER="root"
REMOTE_DIR="/opt/halo-inventory"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> .env ellenőrzése..."
if [[ ! -f "${LOCAL_DIR}/deploy/.env" ]]; then
  echo "HIBA: deploy/.env nem létezik."
  echo "  cp deploy/.env.example deploy/.env  # majd szerkeszd"
  exit 1
fi

echo "==> Kód szinkronizálása ${LXC_HOST}:${REMOTE_DIR}..."
rsync -az --delete \
  --exclude='.git' \
  --exclude='**/.venv' \
  --exclude='**/node_modules' \
  --exclude='**/.next' \
  --exclude='**/__pycache__' \
  --exclude='**/.pytest_cache' \
  --exclude='agents' \
  --exclude='CLAUDE.md' \
  --exclude='WORKFLOW.md' \
  --exclude='USER-GUIDE.md' \
  "${LOCAL_DIR}/" \
  "${LXC_USER}@${LXC_HOST}:${REMOTE_DIR}/"

echo "==> .env feltöltése..."
scp "${LOCAL_DIR}/deploy/.env" "${LXC_USER}@${LXC_HOST}:${REMOTE_DIR}/deploy/.env"

echo "==> Docker Compose build + restart..."
ssh "${LXC_USER}@${LXC_HOST}" bash <<EOF
cd ${REMOTE_DIR}/deploy
docker compose build --pull
docker compose up -d --remove-orphans
docker compose ps
EOF

echo ""
echo "✓ Deploy kész: https://\$(grep APP_DOMAIN ${LOCAL_DIR}/deploy/.env | cut -d= -f2)"
