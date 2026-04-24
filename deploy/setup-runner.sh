#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup-runner.sh — GitHub Actions self-hosted runner telepítése
#
# Futtatás az LXC-n (192.168.1.26):
#   bash deploy/setup-runner.sh <GITHUB_REPO_URL> <REGISTRATION_TOKEN>
#
# Tokent itt szerzed: GitHub repo → Settings → Actions → Runners
#   → New self-hosted runner → Linux x64 → másold a --token értékét
# ─────────────────────────────────────────────────────────────

set -euo pipefail

REPO_URL="${1:-}"
REG_TOKEN="${2:-}"

if [[ -z "$REPO_URL" || -z "$REG_TOKEN" ]]; then
  echo "Használat: $0 <repo-url> <registration-token>"
  echo "Pl.:       $0 https://github.com/felhasznalo/halo-inventory ghp_abc123"
  exit 1
fi

RUNNER_USER="runner"
RUNNER_HOME="/home/${RUNNER_USER}"
RUNNER_DIR="${RUNNER_HOME}/actions-runner"
RUNNER_VERSION="2.322.0"

echo "==> Runner user létrehozása..."
id "$RUNNER_USER" &>/dev/null || useradd -m -s /bin/bash "$RUNNER_USER"

echo "==> Docker csoport hozzáadása..."
usermod -aG docker "$RUNNER_USER"

echo "==> Runner letöltése..."
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"
curl -fsSLO "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
tar xzf "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
rm "actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
chown -R "${RUNNER_USER}:${RUNNER_USER}" "$RUNNER_DIR"

echo "==> Runner konfigurálása..."
sudo -u "$RUNNER_USER" "$RUNNER_DIR/config.sh" \
  --url "$REPO_URL" \
  --token "$REG_TOKEN" \
  --name "halo-inventory-lxc" \
  --labels "self-hosted,linux,halo-inventory" \
  --unattended \
  --replace

echo "==> Systemd service telepítése..."
"$RUNNER_DIR/svc.sh" install "$RUNNER_USER"
"$RUNNER_DIR/svc.sh" start

echo ""
echo "✓ Runner fut: $(systemctl is-active actions.runner.* 2>/dev/null | head -1)"
echo "✓ Ellenőrzés: GitHub repo → Settings → Actions → Runners"
