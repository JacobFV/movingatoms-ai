#!/usr/bin/env bash
# Build the processing image for this machine and run it as a systemd service.
# usage: processing/deploy/install-local.sh   (asks for sudo for the systemd and /etc parts)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
docker build -t movingatoms-processing:latest "$here/.."
sudo install -d -m 700 /etc/movingatoms
if [ ! -f /etc/movingatoms/worker.env ]; then
  sudo install -m 600 "$HOME/.config/movingatoms/worker.env" /etc/movingatoms/worker.env
fi
sudo install -d /var/lib/movingatoms
sudo cp "$here/movingatoms-worker.service" /etc/systemd/system/movingatoms-worker.service
sudo systemctl daemon-reload
sudo systemctl enable --now movingatoms-worker
systemctl --no-pager status movingatoms-worker | head -5
