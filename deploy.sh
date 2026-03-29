#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="/opt/persian-translator-bot"
REPO_URL="https://github.com/aliir74/persian-translator-bot.git"

# Load VPS_SSH from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/.env" ]]; then
    VPS_SSH=$(grep -E "^VPS_SSH=" "$SCRIPT_DIR/.env" | cut -d'=' -f2-)
fi

if [[ -z "${VPS_SSH:-}" ]]; then
    echo "Error: VPS_SSH not set. Add VPS_SSH=user@host to .env"
    exit 1
fi

echo "Deploying to $VPS_SSH:$DEPLOY_PATH ..."

# Sync .env to VPS
scp "$SCRIPT_DIR/.env" "$VPS_SSH:$DEPLOY_PATH/.env" 2>/dev/null || true

ssh "$VPS_SSH" bash -s -- "$DEPLOY_PATH" "$REPO_URL" <<'REMOTE'
set -euo pipefail
DEPLOY_PATH="$1"
REPO_URL="$2"

if [[ ! -d "$DEPLOY_PATH" ]]; then
    echo "Cloning repo..."
    git clone "$REPO_URL" "$DEPLOY_PATH"
else
    echo "Pulling latest..."
    cd "$DEPLOY_PATH"
    git pull --ff-only
fi

cd "$DEPLOY_PATH"

echo "Building and starting..."
docker compose up -d --build

echo "Done! Container status:"
docker compose ps
REMOTE

echo "Deploy complete."
