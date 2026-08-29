#!/bin/sh
# Guided install and update from a checkout or a temporary remote bundle.
# POSIX sh, so `sh setup.sh` works too.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
script_name=${0##*/}
if [ "$script_name" = "setup.sh" ] \
    && [ -f "$script_dir/scripts/install.py" ] \
    && [ -f "$script_dir/scripts/show_baseline_version.py" ] \
    && [ -f "$script_dir/secure-coding-baseline.md" ]; then
    cd "$script_dir"
    exec python3 scripts/install.py --interactive "$@"
fi

command -v curl >/dev/null 2>&1 || {
    echo "curl is required for setup without a checkout." >&2
    exit 1
}
command -v python3 >/dev/null 2>&1 || {
    echo "python3 is required for setup." >&2
    exit 1
}

api_url="https://api.github.com/repos/appsec-foundry/ai-secure-coding-baseline/branches/main"
source_ref=$(
    curl --proto '=https' \
        --fail --silent --show-error --max-time 15 "$api_url" |
        python3 -c '
import json
import re
import sys

payload = json.load(sys.stdin)
commit = payload.get("commit")
sha = commit.get("sha") if isinstance(commit, dict) else None
if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
    raise SystemExit("GitHub did not return a valid main commit")
print(sha)
'
)
case "$source_ref" in
    *[!0-9a-f]* | "")
        echo "GitHub returned an invalid main commit SHA." >&2
        exit 2
        ;;
esac
if [ "${#source_ref}" -ne 40 ]; then
    echo "GitHub returned an invalid main commit SHA." >&2
    exit 2
fi

setup_tmp=$(mktemp -d "${TMPDIR:-/tmp}/aisec-setup.XXXXXX")
cleanup() {
    if [ -d "$setup_tmp" ]; then
        rm -r -- "$setup_tmp"
    fi
}
trap cleanup 0 1 2 3 15
mkdir -p "$setup_tmp/scripts"

source_root="https://raw.githubusercontent.com/appsec-foundry/ai-secure-coding-baseline/$source_ref"
download() {
    curl --proto '=https' \
        --fail --silent --show-error --max-time 30 \
        --output "$setup_tmp/$1" "$source_root/$1"
}

download secure-coding-baseline.md
download scripts/install.py
download scripts/show_baseline_version.py

python3 "$setup_tmp/scripts/install.py" --interactive "$@"
