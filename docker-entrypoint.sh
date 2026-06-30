#!/bin/sh
set -e
python -m ai_mini_box init --force
python -m ai_mini_box db upgrade
exec python -m ai_mini_box "$@"
