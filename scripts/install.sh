#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

install_dir="$HOME/.local/share/nemo-python/extensions"
target="$install_dir/nemo_tab_restore.py"

/usr/bin/python3 -m py_compile nemo_tab_restore.py

mkdir -p "$install_dir"
cp nemo_tab_restore.py "$target"

echo "Installed: $target"
echo
echo "Restart Nemo to load the extension:"
echo "  nemo -q"
echo "  nemo &"
