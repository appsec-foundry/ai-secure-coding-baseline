#!/usr/bin/env bash
# Guided install and update, for anyone who looks for a setup script instead of
# a make target. Same flow as `make setup`; the logic lives in the Python
# installer, not here.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 scripts/install.py --interactive "$@"
