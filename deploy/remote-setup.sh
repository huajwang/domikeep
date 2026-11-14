#!/bin/bash
set -euo pipefail

apt-get update
apt-get install -y python3-venv nginx certbot python3-certbot-nginx
python3 -c 'import sys; assert sys.version_info >= (3, 10), sys.version'

tar -xzf /tmp/domikeep-src.tgz -C /opt

if ! id domikeep >/dev/null 2>&1; then
    useradd --system --home-dir /opt/domikeep --shell /usr/sbin/nologin domikeep
fi

mkdir -p /var/lib/domikeep/media /var/backups/domikeep
chown -R domikeep:domikeep /opt/domikeep /var/lib/domikeep /var/backups/domikeep

sudo -u domikeep python3 -m venv /opt/domikeep/.venv
sudo -u domikeep /opt/domikeep/.venv/bin/pip install -r /opt/domikeep/requirements.txt

if [ ! -f /etc/domikeep.env ]; then
    key="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
    cat > /etc/domikeep.env <<EOF
DEBUG=0
SECRET_KEY=${key}
ALLOWED_HOSTS=domikeep.com,www.domikeep.com,emall.domikeep.com,localhost,127.0.0.1
SHOP_HOSTS=emall.domikeep.com
COMPANY_ORIGIN=https://domikeep.com
SHOP_ORIGIN=https://emall.domikeep.com
CSRF_TRUSTED_ORIGINS=https://domikeep.com,https://www.domikeep.com,https://emall.domikeep.com
DATABASE_PATH=/var/lib/domikeep/db.sqlite3
MEDIA_ROOT=/var/lib/domikeep/media
DOMIKEEP_EMAIL=hello@domikeep.com
DOMIKEEP_PHONE=
FLAT_SHIPPING_CENTS=1500
FREE_SHIPPING_CENTS=15000
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PUBLISHABLE_KEY=
EOF
fi
chown root:domikeep /etc/domikeep.env
chmod 640 /etc/domikeep.env

sudo -u domikeep bash -c 'set -a; source /etc/domikeep.env; set +a; cd /opt/domikeep; .venv/bin/python manage.py migrate; .venv/bin/python manage.py collectstatic --noinput'

cp /opt/domikeep/deploy/domikeep.service /etc/systemd/system/domikeep.service
cp /opt/domikeep/deploy/domikeep-backup.service /etc/systemd/system/domikeep-backup.service
cp /opt/domikeep/deploy/domikeep-backup.timer /etc/systemd/system/domikeep-backup.timer
if ! grep -q ssl_certificate /etc/nginx/sites-available/domikeep 2>/dev/null; then
    cp /opt/domikeep/deploy/nginx-domikeep.conf /etc/nginx/sites-available/domikeep
fi
ln -sfn /etc/nginx/sites-available/domikeep /etc/nginx/sites-enabled/domikeep

systemctl daemon-reload
systemctl enable --now domikeep.service domikeep-backup.timer
nginx -t
systemctl reload nginx

echo "setup-complete"
systemctl is-active domikeep.service
curl -s -o /dev/null -w "company %{http_code}\n" -H "Host: domikeep.com" http://127.0.0.1/
curl -s -o /dev/null -w "shop %{http_code}\n" -H "Host: emall.domikeep.com" http://127.0.0.1/
curl -s -o /dev/null -w "voice %{http_code}\n" -H "Host: voice.yaojiabuy.com" http://127.0.0.1/
