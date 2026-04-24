#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# setup-lxc.sh — Egyszer kell futtatni
# Létrehoz egy új LXC-t Proxmox-on, telepíti a Docker-t, és
# beállítja a Cloudflare Tunnel route-ot.
#
# Futtatás: bash deploy/setup-lxc.sh
# Előfeltétel: SSH kulcs a Proxmox host-on (192.168.1.2)
# ─────────────────────────────────────────────────────────────

set -euo pipefail

PROXMOX_HOST="192.168.1.2"
PROXMOX_USER="root"
LXC_ID="106"
LXC_IP="192.168.1.26"
LXC_GW="192.168.1.1"
LXC_HOSTNAME="halo-inventory"
LXC_CORES="2"
LXC_MEM="1024"       # MB
LXC_DISK="8"         # GB
LXC_STORAGE="local-lvm"
LXC_BRIDGE="vmbr1"
APP_DOMAIN="halo-leltar.otthonkapocs.hu"

# Az SSH public kulcsod — ez kerül a root@LXC-be
SSH_PUBKEY="${HOME}/.ssh/id_rsa.pub"

echo "==> SSH kulcs ellenőrzése..."
if [[ ! -f "$SSH_PUBKEY" ]]; then
  echo "HIBA: ${SSH_PUBKEY} nem található. Adjad meg a helyes elérési utat."
  exit 1
fi
PUBKEY_CONTENT=$(cat "$SSH_PUBKEY")

echo "==> LXC template keresése Proxmox-on..."
TEMPLATE=$(ssh "${PROXMOX_USER}@${PROXMOX_HOST}" \
  "pveam list local | grep 'debian-12' | tail -1 | awk '{print \$1}'" 2>/dev/null || true)

if [[ -z "$TEMPLATE" ]]; then
  echo "  Debian 12 template nincs letöltve, letöltöm..."
  ssh "${PROXMOX_USER}@${PROXMOX_HOST}" "pveam download local debian-12-standard_12.7-1_amd64.tar.zst"
  TEMPLATE="local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst"
fi

echo "==> LXC ${LXC_ID} létrehozása (${LXC_IP})..."
ssh "${PROXMOX_USER}@${PROXMOX_HOST}" bash <<EOF
pct create ${LXC_ID} ${TEMPLATE} \
  --hostname ${LXC_HOSTNAME} \
  --cores ${LXC_CORES} \
  --memory ${LXC_MEM} \
  --rootfs ${LXC_STORAGE}:${LXC_DISK} \
  --net0 name=eth0,bridge=${LXC_BRIDGE},ip=${LXC_IP}/24,gw=${LXC_GW} \
  --nameserver 192.168.1.25 \
  --features nesting=1,keyctl=1 \
  --unprivileged 1 \
  --onboot 1 \
  --start 1
EOF

echo "==> LXC indulásra vár (10s)..."
sleep 10

echo "==> SSH kulcs beinjektálása az LXC-be..."
ssh "${PROXMOX_USER}@${PROXMOX_HOST}" bash <<EOF
pct exec ${LXC_ID} -- bash -c "
  mkdir -p /root/.ssh
  echo '${PUBKEY_CONTENT}' >> /root/.ssh/authorized_keys
  chmod 700 /root/.ssh
  chmod 600 /root/.ssh/authorized_keys
"
EOF

echo "==> Docker telepítése az LXC-ben..."
ssh "${PROXMOX_USER}@${PROXMOX_HOST}" bash <<PROXEOF
pct exec ${LXC_ID} -- bash -c "
  apt-get update -q
  apt-get install -y -q ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable' \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable docker
  systemctl start docker
"
PROXEOF

echo "==> App könyvtár létrehozása..."
ssh "${PROXMOX_USER}@${PROXMOX_HOST}" \
  "pct exec ${LXC_ID} -- mkdir -p /opt/halo-inventory"

echo "==> Cloudflare Tunnel route hozzáadása..."
ssh "${PROXMOX_USER}@${PROXMOX_HOST}" bash <<EOF
# Ingress sort szúr be a catch-all (404) sor elé
if grep -q "${APP_DOMAIN}" /etc/cloudflared/config.yml; then
  echo "  Tunnel route már létezik, kihagyva."
else
  sed -i '/- service: http_status:404/i\\  - hostname: ${APP_DOMAIN}\n    service: http://${LXC_IP}:80' \
    /etc/cloudflared/config.yml
  systemctl restart cloudflared
  echo "  Tunnel route hozzáadva és cloudflared újraindítva."
fi
EOF

echo ""
echo "✓ LXC ${LXC_ID} kész: ${LXC_IP}"
echo "✓ Tunnel route: https://${APP_DOMAIN} → http://${LXC_IP}:80"
echo ""
echo "Következő lépés:"
echo "  1. Cloudflare DNS-ben adj hozzá CNAME: ${APP_DOMAIN} → <tunnel-id>.cfargotunnel.com"
echo "  2. Másold a .env fájlt: cp deploy/.env.example deploy/.env && szerkeszd"
echo "  3. Futtasd: bash deploy/deploy.sh"
