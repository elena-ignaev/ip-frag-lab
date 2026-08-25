#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
.venv/bin/pyinstaller --noconfirm --windowed --name IPFragLab \
  --add-data "ipfrag:ipfrag" \
  qt_app.py
echo "Built dist/IPFragLab.app (macOS) or dist/IPFragLab/"
