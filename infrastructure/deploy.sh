#!/bin/bash
# ==============================================================================
# SecurATS - Deployment (Django + Docker Compose)
# ==============================================================================
# Kanonischer Stack ist Django (siehe NORTHSTAR.md, Abschnitt 6). Der frühere
# Next.js/pm2-Ablauf ist nach legacy/ ausgelagert.
# Voraussetzung: eine .env mit DJANGO_SECRET_KEY und PII_ENCRYPTION_KEY
# (siehe .env.example). Migrationen laufen im Container-Entrypoint.
# ==============================================================================

set -e

echo "[SecurATS] Deployment startet..."

echo "[1/3] Lade neuesten Code..."
git fetch origin main
git reset --hard origin/main

echo "[2/3] Baue das Django-Image..."
docker compose build web

echo "[3/3] Rolle Container neu aus (Migrationen laufen im Entrypoint)..."
docker compose up -d web
docker image prune -f >/dev/null 2>&1 || true

echo "[SecurATS] Deployment erfolgreich abgeschlossen."
