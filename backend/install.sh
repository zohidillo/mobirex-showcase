#!/usr/bin/env bash
# Mobirex production boshlang'ich deploy
# Bir martalik. Keyingi update'lar uchun README.deploy.md ga qarang.

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}==>${NC} $*"; }
warn() { echo -e "${YELLOW}!! ${NC} $*"; }
err()  { echo -e "${RED}xx ${NC} $*" >&2; }

NETWORK_NAME="mobirex_network"
STATIC_VOLUME="mobirex_static_files"
MEDIA_VOLUME="mobirex_media_files"
APPUSER_UID=1000

# Domains
DOMAIN_APEX="mobirex.uz"
DOMAIN_WWW="www.mobirex.uz"
DOMAIN_API="api.mobirex.uz"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@mobirex.uz}"

cd "$(dirname "$0")"
BACKEND_DIR="$(pwd)"
PARENT_DIR="$(dirname "$BACKEND_DIR")"
BOT_DIR="$PARENT_DIR/bot"
LANDING_DIR="$PARENT_DIR/landing"

# ============================================================
# 1. Tekshiruvlar
# ============================================================
log "1/13 Boshlang'ich tekshiruvlar..."

if ! command -v docker &>/dev/null; then
    err "Docker o'rnatilmagan."
    exit 1
fi

if ! docker compose version &>/dev/null; then
    err "Docker Compose v2 kerak."
    exit 1
fi

if ! docker info &>/dev/null; then
    err "Docker daemon ishlamayapti."
    exit 1
fi

# ============================================================
# 2. Eski certbot container'larni tozalash (asosiy fix)
# ============================================================
log "2/13 Eski certbot container'larni tozalash..."

OLD_CERTBOTS=$(docker ps -aq --filter "name=certbot" 2>/dev/null || true)
if [ -n "$OLD_CERTBOTS" ]; then
    warn "Eski certbot container'lar topildi, o'chirilmoqda..."
    docker rm -f $OLD_CERTBOTS 2>/dev/null || true
fi

# ============================================================
# 3. Host port 80/443
# ============================================================
log "3/13 Host portlarini tekshirish..."

PORT_BUSY=""
if command -v ss &>/dev/null; then
    if ss -tlnH '( sport = :80 )' 2>/dev/null | grep -q LISTEN; then
        # Docker proxy bo'lsa OK, host nginx bo'lsa muammo
        if ! docker ps --format '{{.Names}}' | grep -q mobirex_nginx; then
            PORT_BUSY="80"
        fi
    fi
fi

if [ -n "$PORT_BUSY" ]; then
    warn "Host port $PORT_BUSY band (Docker emas)."
    warn "Tuzatish: sudo systemctl stop nginx"
    read -r -p "Davom etamizmi? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        exit 0
    fi
fi

# ============================================================
# 4. .env fayllar
# ============================================================
log "4/13 .env fayllarni tekshirish..."

if [ ! -f "$BACKEND_DIR/.env.dev" ]; then
    err "$BACKEND_DIR/.env.dev yo'q."
    exit 1
fi

SECRET_KEY_VAL="$(grep -E '^SECRET_KEY=' "$BACKEND_DIR/.env.dev" | head -n1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
if [ ${#SECRET_KEY_VAL} -lt 50 ]; then
    err "SECRET_KEY juda qisqa (${#SECRET_KEY_VAL} belgi, kamida 50 kerak)."
    exit 1
fi

if [ ! -f "$BOT_DIR/.env" ]; then
    err "$BOT_DIR/.env yo'q."
    exit 1
fi

# ============================================================
# 5. Landing papkasi
# ============================================================
log "5/13 Landing papkasi tekshirish..."

if [ ! -d "$LANDING_DIR" ] || [ ! -f "$LANDING_DIR/index.html" ]; then
    err "$LANDING_DIR/index.html yo'q."
    exit 1
fi

# ============================================================
# 6. Docker network
# ============================================================
log "6/13 Docker tarmoq: $NETWORK_NAME"

if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
    docker network create "$NETWORK_NAME"
else
    warn "Tarmoq $NETWORK_NAME mavjud."
fi

# ============================================================
# 7. Volumes
# ============================================================
log "7/13 Volumes: $STATIC_VOLUME, $MEDIA_VOLUME"

for V in "$STATIC_VOLUME" "$MEDIA_VOLUME"; do
    if ! docker volume inspect "$V" &>/dev/null; then
        docker volume create "$V" >/dev/null
        docker run --rm -v "$V":/data alpine sh -c "chown -R $APPUSER_UID:$APPUSER_UID /data && chmod 755 /data"
    else
        warn "Volume $V mavjud."
    fi
done

# ============================================================
# 8. Certbot papkalari
# ============================================================
log "8/13 Certbot papkalari"
mkdir -p "$BACKEND_DIR/certbot/conf" "$BACKEND_DIR/certbot/www"

# ============================================================
# 9. Backend
# ============================================================
log "9/13 Backend container'larni qurish va ishga tushirish..."
cd "$BACKEND_DIR"
docker compose up -d --build

log "    Migration va collectstatic'ni kutish (~30s)..."
sleep 30

# ============================================================
# 10. Bot
# ============================================================
log "10/13 Bot container'larni ishga tushirish..."
cd "$BOT_DIR"
docker compose up -d --build
cd "$BACKEND_DIR"

# ============================================================
# 11. DNS tasdiqlash
# ============================================================
log "11/13 SSL sertifikat olish..."

PUBLIC_IP="$(curl -4 -fsS --max-time 5 https://ifconfig.me || echo 'unknown')"
echo ""
warn "DNS A-record'lar shu IP ga ishora qilishi kerak: ${PUBLIC_IP}"
echo "  ${DOMAIN_APEX}    -> ${PUBLIC_IP}"
echo "  ${DOMAIN_WWW}     -> ${PUBLIC_IP}"
echo "  ${DOMAIN_API}     -> ${PUBLIC_IP}"
echo ""
read -r -p "DNS to'g'ri sozlanganmi? (y/N): " DNS_OK
if [ "$DNS_OK" != "y" ] && [ "$DNS_OK" != "Y" ]; then
    warn "To'xtatildi. DNS sozlanganidan keyin qaytadan ishga tushiring."
    exit 0
fi

# Mavjud sertifikat tekshirish — qayta urinish kerak emas
if [ -d "$BACKEND_DIR/certbot/conf/live/$DOMAIN_APEX" ]; then
    warn "Sertifikat allaqachon mavjud: certbot/conf/live/$DOMAIN_APEX"
    read -r -p "Qayta olishni xohlaysizmi? (y/N): " RENEW
    if [ "$RENEW" != "y" ] && [ "$RENEW" != "Y" ]; then
        log "    Sertifikat o'tkazib yuborildi, to'g'ridan-to'g'ri nginx restart..."
        # Bootstrap config bo'lsa olib tashlash
        rm -f nginx/conf.d/_initial.conf
        shopt -s nullglob
        for f in nginx/conf.d/*.conf.disabled; do
            mv "$f" "${f%.disabled}"
        done
        shopt -u nullglob

        # Nginx restart
        if docker ps --format '{{.Names}}' | grep -q mobirex_nginx; then
            docker compose -f docker-compose.nginx.yml restart nginx
        else
            docker compose -f docker-compose.nginx.yml up -d
        fi

        echo ""
        log "13/13 Deploy tugadi!"
        echo ""
        echo "Tekshirish:"
        echo "  curl -I https://${DOMAIN_APEX}"
        echo "  curl -I https://${DOMAIN_API}/api/me/"
        exit 0
    fi
fi

# ============================================================
# 12. Bootstrap nginx + certbot
# ============================================================
log "12/13 Vaqtinchalik nginx ishga tushirish..."

# Asosiy config'larni vaqtinchalik o'chirish
shopt -s nullglob
for f in nginx/conf.d/*.conf; do
    case "$(basename "$f")" in
        _initial.conf) continue ;;
    esac
    mv "$f" "${f}.disabled"
done
shopt -u nullglob

# Bootstrap config
if [ -f nginx/conf.d/_initial.conf.template ]; then
    cp nginx/conf.d/_initial.conf.template nginx/conf.d/_initial.conf
fi

# Nginx start (yoki restart)
if docker ps --format '{{.Names}}' | grep -q mobirex_nginx; then
    docker compose -f docker-compose.nginx.yml restart nginx
else
    docker compose -f docker-compose.nginx.yml up -d nginx
fi
sleep 5

# ============================================================
# CERTBOT — docker run bilan (compose run o'rniga)
# Bu eng katta fix — interactive log ko'rinadi
# ============================================================
log "    Certbot certonly (docker run bilan)..."

docker run --rm \
    --name certbot_install \
    -v "$BACKEND_DIR/certbot/conf:/etc/letsencrypt" \
    -v "$BACKEND_DIR/certbot/www:/var/www/certbot" \
    certbot/certbot:latest \
    certonly \
    --webroot --webroot-path=/var/www/certbot \
    --email "$CERTBOT_EMAIL" \
    --agree-tos --no-eff-email \
    -d "$DOMAIN_APEX" -d "$DOMAIN_WWW" -d "$DOMAIN_API"

CERTBOT_EXIT=$?

if [ $CERTBOT_EXIT -ne 0 ]; then
    err "Certbot xato bilan tugadi (exit code: $CERTBOT_EXIT)"
    err "Tekshirish: docker logs certbot_install (agar mavjud bo'lsa)"
    exit 1
fi

# Bootstrap'ni olib tashlash, asosiy config'larni qaytarish
rm -f nginx/conf.d/_initial.conf
shopt -s nullglob
for f in nginx/conf.d/*.conf.disabled; do
    mv "$f" "${f%.disabled}"
done
shopt -u nullglob

log "    Nginx restart (full config bilan)..."
docker compose -f docker-compose.nginx.yml restart nginx

# Certbot auto-renewal container (background)
docker compose -f docker-compose.nginx.yml up -d certbot

# ============================================================
# 13. Yakuniy hisobot
# ============================================================
echo ""
log "13/13 Deploy muvaffaqiyatli tugadi!"
echo ""
echo "Tekshirish:"
echo "  curl -I https://${DOMAIN_APEX}        # 200 OK"
echo "  curl -I https://${DOMAIN_API}/api/me/ # 401 (auth kerak)"
echo ""
echo "Foydali komandalar:"
echo "  docker compose -f $BACKEND_DIR/docker-compose.yml logs -f web"
echo "  docker compose -f $BACKEND_DIR/docker-compose.nginx.yml logs -f nginx"
echo "  docker compose -f $BOT_DIR/docker-compose.yml logs -f"