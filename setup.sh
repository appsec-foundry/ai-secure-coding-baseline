#!/bin/sh
# Guided install and update, for anyone who looks for a setup script instead of
# a make target. Same flow as `make setup`; the logic lives in the Python
# installer, not here. POSIX sh, so `sh setup.sh` works too.
set -eu
cd "$(dirname "$0")"
exec python3 scripts/install.py --interactive "$@"
