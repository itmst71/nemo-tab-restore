# Nemo Tab Restore

[日本語版](README.ja.md)

Nemo Tab Restore is a `nemo-python` extension that adds browser-like closed-tab restoration to the Nemo file manager.

It saves the current tab URI when a tab is closed with `Ctrl+W`, and restores the most recently closed tab with `Ctrl+Shift+T`.

## Features

- Saves the current tab URI when `Ctrl+W` or Nemo's configured close shortcut is pressed
- Lets Nemo continue handling the normal close-tab action
- Restores the most recently closed tab with `Ctrl+Shift+T`
- Persists history as JSON Lines
- Checks local path existence before restoring `file://` URIs, and skips missing paths
- Passes non-`file://` URIs directly to Nemo
- Supports environment variables for logging and history size

## Requirements

Linux Mint / Ubuntu family:

The following package names are confirmed on Linux Mint 22 and Ubuntu 24.04 / 26.04-family systems:

```bash
sudo apt install nemo-python gir1.2-nemo-3.0 python3-gi python3-gi-cairo
```

Linux Mint usually ships Nemo by default, but the Python extension bindings and GI packages may still be needed.

On other Ubuntu-family releases, package names are expected to be similar. If installation fails, check the available package names with `apt search nemo-python` and `apt search gir1.2-nemo`.

openSUSE Tumbleweed:

```bash
sudo zypper install python3-nemo typelib-1_0-Nemo-3_0
```

On Tumbleweed, `python3-nemo` currently pulls the matching Python GObject packages as dependencies.

Arch Linux:

```bash
sudo pacman -S nemo nemo-python
```

On Arch Linux, `nemo` currently pulls `python-gobject` and `python-cairo` as dependencies.

## Install

Install with the helper script:

```bash
./scripts/install.sh
```

Or install manually:

```bash
mkdir -p ~/.local/share/nemo-python/extensions
cp nemo_tab_restore.py ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

Restart Nemo:

```bash
nemo -q
nemo &
```

You can also start Nemo normally from the desktop launcher after quitting it with `nemo -q`.

## Uninstall

Uninstall with the helper script:

```bash
./scripts/uninstall.sh
```

The uninstall script removes only the installed extension file. History and logs are kept.

Or remove the installed extension manually:

```bash
rm ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

## Usage

### Close tab

```text
Ctrl+W
```

The extension saves the current tab URI to history, then returns `False` so Nemo can perform its normal close-tab action.

### Restore last closed tab

```text
Ctrl+Shift+T
```

The extension pops the most recently closed URI from history and restores it in the existing Nemo window with:

```bash
nemo --existing-window --tabs URI
```

The background context menu also includes `Restore Last Closed Tab`.

## Files

Extension install path:

```text
~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

History file:

```text
~/.local/share/nemo-tab-restore/closed-tabs.jsonl
```

Log file:

```text
~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

## Configuration

### Logging

```bash
NEMO_TAB_RESTORE_LOG=1 nemo
NEMO_TAB_RESTORE_LOG=0 nemo
```

For debugging, start Nemo from a terminal with logging enabled:

```bash
nemo -q
NEMO_TAB_RESTORE_LOG=1 nemo
```

Enabled values:

```text
1
true
yes
on
debug
```

Disabled values:

```text
0
false
no
off
empty string
```

Logging is disabled by default.

### History size

```bash
NEMO_TAB_RESTORE_MAX_HISTORY=300 nemo
```

Defaults and limits:

```text
default: 100
min: 1
max: 1000
```

Invalid values, empty values, and values below the minimum fall back to the default. Values above the maximum are clamped to `1000`.

## Shortcuts

The extension reads Nemo / GTK accel maps.

Candidate paths:

```text
$XDG_CONFIG_HOME/nemo/accels/nemo
$XDG_CONFIG_HOME/gtk-3.0/accels/nemo
~/.config/nemo/accels/nemo
~/.gnome2/accels/nemo
~/.config/gtk-3.0/accels/nemo
```

`$XDG_CONFIG_HOME` paths are checked first when the variable is set and non-empty.

Close action:

```text
<Actions>/ShellActions/Close
```

Default:

```text
<Primary>w
```

Restore action:

```text
<Actions>/NemoTabRestore/RestoreLastClosedTab
```

Default:

```text
<Primary><Shift>t
```

This default intentionally follows the browser convention for restoring a closed tab. Nemo also defines `<Primary><Shift>t` as the default accelerator for `<Actions>/DirViewActions/OpenInNewTab`, which opens selected items in new tabs. If you rely on Nemo's original binding, change this extension's restore accelerator to another shortcut in the accel file.

To explicitly set the restore shortcut, add this line to the Nemo accel file:

```scheme
(gtk_accel_path "<Actions>/NemoTabRestore/RestoreLastClosedTab" "<Primary><Shift>t")
```

## Check

Syntax check:

```bash
/usr/bin/python3 -m py_compile nemo_tab_restore.py
```

## Debugging

Start Nemo with logging enabled:

```bash
nemo -q
sleep 1
rm -f ~/.cache/nemo-tab-restore/nemo-tab-restore.log
NEMO_TAB_RESTORE_LOG=1 nemo &
```

Inspect the log:

```bash
tail -f ~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

Expected window hook:

```text
hooked window wid=0x... uri=file:///... title='Loading...'
```

## Known limitations

- Only keyboard close shortcuts are tracked.
- Mouse-based tab close operations are not tracked.
- Out of scope operations:
  - tab close button
  - middle-click tab close
  - tab context menu close
- Full open-tab enumeration is not implemented.
- This is a Nemo extension, not a Nautilus or Caja extension.

## Troubleshooting

### `No module named 'gi'`

Nemo Python extensions use GI / PyGObject.

Nemo loads Python extensions with the distribution Python environment. If another Python installation is first in `PATH`, `gi` may fail to import even though it works with the distribution Python.

Check:

```bash
which -a python3
python3 --version
python3 -c 'import gi; print(gi.__file__)'
```

Expected example:

```text
/usr/bin/python3
/usr/lib/python3/dist-packages/gi/__init__.py
```

When debugging GI import problems, check the distribution Python directly:

```bash
/usr/bin/python3 -c 'import gi; print(gi.__file__)'
```

## Behavior details

- The close shortcut saves the current URI, then lets Nemo continue with the normal close action.
- The restore shortcut pops a URI from history and opens it in the existing Nemo window.
- Each key press is handled separately, matching browser-like behavior.
- Consecutive duplicate URIs are not suppressed. The same folder can legitimately be open in multiple tabs.

## License

MIT License. See [LICENSE](LICENSE).
