#!/usr/bin/env bash
# Render bu skripti "Build Command" kimi işlədəcək.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
