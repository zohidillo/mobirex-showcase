# Mobirex Production Deploy

Markaziy Docker nginx orqali backend (api.mobirex.uz), landing
(mobirex.uz, www.mobirex.uz) va Telegram bot — bitta `mobirex_network`
ichida.

## Server papka strukturasi

```
~/mobirex/
├── backend/    # Django (web, db, redis, nginx, certbot)
├── landing/    # Static HTML/CSS/JS (nginx mount qilib serve qiladi)
└── bot/        # Telegram support bot (aiogram + SQLite + Redis)
```

## ⚠️ Birinchi navbatda: Telegram token rotation

Repo tarixida `.env.dev` da real `TELEGRAM_BOT_TOKEN` saqlangan
bo'lishi mumkin. Bu **compromise xavfi**.

**Darhol bajaring:**

1. [@BotFather](https://t.me/BotFather) → `/revoke` → eski tokenni bekor
   qilish
2. `/token` → yangi token olish
3. `backend/.env` va `bot/.env` ga yangi tokenni yozish
4. Eski tokendan foydalangan tashqi service'lar (CI, dashboard) ham
   yangilansin
5. `git log -p -- .env.dev` bilan tarixni tekshiring — token ko'rinsa,
   commit'larni rebase bilan tozalash kerak

`.gitignore` endi `.env*` ni e'tiborga olmaydi (faqat `.env.example`).
Yangi `.env` fayllar git'ga tushmaydi.

## Boshlang'ich deploy

1. Server'ga SSH va kerakli paketlar:
```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-plugin curl
   sudo usermod -aG docker $USER
   newgrp docker
```

2. Repolarni `~/mobirex/` ga klon qiling:
```bash
   mkdir -p ~/mobirex && cd ~/mobirex
   git clone <backend-repo> backend
   git clone <landing-repo> landing
   git clone <bot-repo> bot
```

3. `.env` fayllarni to'ldiring:
```bash
   cd ~/mobirex/backend
   cp .env.example .env
   nano .env
   # SECRET_KEY (>=50 char), DB_*, REDIS_*, ALLOWED_HOSTS,
   # CORS_ALLOWED_ORIGINS, TELEGRAM_BOT_TOKEN, ...

   cd ~/mobirex/bot
   cp .env.example .env
   nano .env
   # BOT_TOKEN, SUPPORT_GROUP_ID, REDIS_URL
```

4. install.sh:
```bash
   cd ~/mobirex/backend
   chmod +x install.sh
   ./install.sh
```

   Script:
   - Docker va port 80/443 tekshirishi
   - `.env` minimal validatsiyasi (SECRET_KEY uzunligi)
   - `mobirex_network` va `mobirex_static_files`, `mobirex_media_files`
     volumes yaratishi
   - Backend va bot container'lar build + up
   - DNS tasdig'ini so'rashi (mobirex.uz, www.mobirex.uz, api.mobirex.uz
     A-record'lar)
   - Certbot orqali Let's Encrypt SSL olish
   - Nginx full config bilan restart
   - Auto-renew certbot container ishga tushirish

## Yangilanish (update)

```bash
# Backend
cd ~/mobirex/backend
git pull
docker compose up -d --build
# entrypoint avtomatik migrate + collectstatic qiladi

# Landing
cd ~/mobirex/landing
git pull
# Hech narsa qilish shart emas — nginx volume mount, fayllar darhol
# yangilanadi. Brauzer cache uchun assets'da version query kerak.

# Bot
cd ~/mobirex/bot
git pull
docker compose up -d --build

# Nginx config o'zgargan bo'lsa
cd ~/mobirex/backend
docker compose -f docker-compose.nginx.yml restart nginx
```

## SSL yangilash

Certbot container 12 soat sayin `certbot renew --webroot` chaqiradi.
Qo'lda majburiy yangilash:

```bash
cd ~/mobirex/backend
docker compose -f docker-compose.nginx.yml run --rm certbot renew --force-renewal
docker compose -f docker-compose.nginx.yml restart nginx
```

## Verification

```bash
# Tarmoq va container'lar
docker network ls | grep mobirex
docker compose -f ~/mobirex/backend/docker-compose.yml ps
docker compose -f ~/mobirex/backend/docker-compose.nginx.yml ps
docker compose -f ~/mobirex/bot/docker-compose.yml ps

# HTTP
curl -I https://mobirex.uz                  # 200
curl -I https://www.mobirex.uz              # 301 -> mobirex.uz
curl -I https://api.mobirex.uz/api/me/      # 401 (auth kerak, to'g'ri)

# Static fayllar
curl -I https://api.mobirex.uz/static/admin/css/base.css  # 200

# Logs
docker compose -f ~/mobirex/backend/docker-compose.yml logs --tail 50 web
docker compose -f ~/mobirex/backend/docker-compose.nginx.yml logs --tail 50 nginx
docker compose -f ~/mobirex/bot/docker-compose.yml logs --tail 50 support_bot
```

## Backup

```bash
# Postgres
docker exec mobirex_backend-db-1 pg_dump -U crm_user crm_db | gzip > backup-$(date +%F).sql.gz

# Media
docker run --rm -v mobirex_media_files:/data -v "$PWD":/backup alpine \
    tar czf /backup/media-$(date +%F).tar.gz -C /data .

# Bot SQLite (bind mount, oddiy fayl)
cp ~/mobirex/bot/data/support_bot.db ~/backup/bot-$(date +%F).db
```

## Eslatma — eski crm.b26.uz

`backend/nginx/crm.conf` va `backend/nginx/mobirex.conf` — eski
HOST-darajadagi nginx config'lar (Docker emas). Yangi setup ularga
tegmaydi (faqat `backend/nginx/conf.d/*.conf` Docker nginx tomonidan
o'qiladi).

Eski `crm.b26.uz` host nginx bilan ishlasa, port 80/443 to'qnashuvi
yuzaga keladi. install.sh boshida buni tekshiradi va sizdan tasdiq
so'raydi.

Eski crm.b26.uz'ni to'liq Docker'ga ko'chirishni xohlasangiz, alohida
task — bu deploy bunga tegmaydi.

## Troubleshooting

**Nginx ishga tushmayapti — port band:**
```bash
sudo ss -tlnp | grep -E ':80 |:443 '
sudo systemctl stop nginx   # host nginx bo'lsa
```

**Static fayllar 404:**
```bash
# Volume'da fayl bormi?
docker run --rm -v mobirex_static_files:/data alpine ls -la /data | head
# Bo'sh bo'lsa, collectstatic qayta:
docker compose exec web python manage.py collectstatic --noinput
```

**Certbot ishlamadi:**
- DNS hali tarqamagan bo'lishi mumkin (`dig +short mobirex.uz`)
- Rate limit (Let's Encrypt 5 fail/hour/domain) — `--staging` bilan test
- Port 80 host'da band emasligini tasdiqlang

**Bot connect bo'lmayapti:**
- `bot/.env` BOT_TOKEN to'g'ri
- `REDIS_URL=redis://bot_redis:6379/0` (default)
- `docker compose -f bot/docker-compose.yml logs support_bot`
