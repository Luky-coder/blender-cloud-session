#!/usr/bin/env bash
# Raccourci : bash tools/build.sh models/<nom> [--samples 32] [--width 800 --height 600] [--views ...] [--no-render]
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-blender}"
exec "$BLENDER" -b --factory-startup -q --python-exit-code 1 -P tools/build.py -- "$@"
