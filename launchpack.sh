#!/bin/sh
# LaunchPack launcher for macOS and Linux
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
if [ $# -gt 0 ]; then
  exec $PY launchpack.py "$@"
fi
exec $PY launchpack_web.py
