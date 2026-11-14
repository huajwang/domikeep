#!/bin/bash
# Run as root on Thunder-na after this project is at /opt/domikeep.
# Attach the Lightsail static IP and point domikeep.com, www, and emall
# at it before running certbot. Edit /etc/domikeep.env before the first
# public start, and create the staff user with manage.py createsuperuser.
set -euo pipefail

if ! id domikeep >/dev/null 2>&1; then
    useradd --system --home-dir /opt/domikeep --shell /usr/sbin/nologin domikeep
fi

apt-get update
apt-get install -y python3-venv nginx certbot python3-certbot-nginx
python3 -c 'import sys; assert sys.version_info >= (3, 10), sys.version'

mkdir -p /var/lib/domikeep/media /var/backups/domikeep
chown -R domikeep:domikeep /opt/domikeep /var/lib/domikeep /var/backups/domikeep

sudo -u domikeep python3 -m venv /opt/domikeep/.venv
sudo -u domikeep /opt/domikeep/.venv/bin/pip install -r /opt/domikeep/requirements.txt

if [ ! -f /etc/domikeep.env ]; then
    cp /opt/domikeep/deploy/env.example /etc/domikeep.env
    echo "Edit /etc/domikeep.env and set SECRET_KEY before serving traffic."
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

echo "When DNS answers for the three names, run:"
echo "  certbot --nginx -d domikeep.com -d www.domikeep.com -d emall.domikeep.com"
