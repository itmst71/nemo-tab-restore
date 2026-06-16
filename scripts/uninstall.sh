#!/usr/bin/env bash
set -euo pipefail

target="$HOME/.local/share/nemo-python/extensions/nemo_tab_restore.py"

if [ -e "$target" ]; then
  rm "$target"
  echo "Removed: $target"
else
  echo "Not installed: $target"
fi

echo
echo "Restart Nemo to unload the extension:"
echo "  nemo -q"
echo "  nemo &"
echo
echo "History and logs were kept:"
echo "  $HOME/.local/share/nemo-tab-restore/closed-tabs.jsonl"
echo "  $HOME/.cache/nemo-tab-restore/nemo-tab-restore.log"
