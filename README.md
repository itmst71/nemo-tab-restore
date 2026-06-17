# Nemo Tab Restore

[日本語版](README.ja.md)

Nemo Tab Restore is a `nemo-python` extension that adds browser-like closed-tab restoration to the Nemo file manager.

Tabs closed with `Ctrl+W` can be restored with `Ctrl+Shift+T`.

## Features

- Saves history for tabs closed with `Ctrl+W`
- Restores the most recently closed tab with `Ctrl+Shift+T`
- Supports changing shortcuts through Nemo's standard accelerator mechanism
- Supports configuring the history limit with an environment variable

## Requirements

In addition to Nemo itself, this extension needs the Python bindings that let Nemo load Python extensions, plus the GI / PyGObject packages used by those bindings. Some distributions pull part of this stack through the Nemo package itself, so the number of extra packages may vary by environment.

### Linux Mint / Ubuntu family

The following package names are confirmed on Linux Mint 22 and Ubuntu 24.04 / 26.04-family systems:

```bash
sudo apt install nemo-python gir1.2-nemo-3.0 python3-gi python3-gi-cairo
```

Linux Mint usually ships Nemo by default, but the Python extension bindings and GI packages may still be needed.

On other Ubuntu-family releases, package names are expected to be similar. If installation fails, check the available package names with `apt search nemo-python` and `apt search gir1.2-nemo`.

### openSUSE Tumbleweed

```bash
sudo zypper install python3-nemo typelib-1_0-Nemo-3_0
```

On Tumbleweed, installing `python3-nemo` also installs the matching Python GObject packages.

### Arch Linux

```bash
sudo pacman -S nemo nemo-python
```

On Arch Linux, installing `nemo` also installs `python-gobject` and `python-cairo`.

## Install

Install manually:

```bash
mkdir -p ~/.local/share/nemo-python/extensions
cp nemo_tab_restore.py ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

A helper script is also available to automate the commands above:

```bash
./scripts/install.sh
```

After installing, quit Nemo completely and start it again. Newly installed extensions are not loaded until Nemo is restarted.

```bash
nemo -q
nemo &
```

You can also start Nemo normally from the desktop launcher after quitting it with `nemo -q`.

## Uninstall

Remove the installed extension manually:

```bash
rm ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

A helper script is also available to automate the command above:

```bash
./scripts/uninstall.sh
```

The uninstall script removes only the installed extension file. History and logs are kept.

## Usage

### Close tab

```text
Ctrl+W
```

The extension saves the current tab URI to history, then Nemo closes the tab normally.

Tabs closed with mouse actions are not saved to history. See [Known limitations](#known-limitations) for details.

### Restore last closed tab

```text
Ctrl+Shift+T
```

The extension pops the most recently closed URI from history and restores the tab.

Internally, it opens the tab in the existing Nemo window with:

```bash
nemo --existing-window --tabs URI
```

Nemo's menu also includes `Restore Last Closed Tab`.

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

Configuration is done with environment variables. For a temporary setting, pass the variable when starting Nemo from a terminal. For persistent settings, add the variable to a suitable startup file for your shell or desktop environment, such as `~/.profile`.

### Logging

```bash
NEMO_TAB_RESTORE_LOG=true nemo
NEMO_TAB_RESTORE_LOG=false nemo
```

Use `true` or `false` in normal use. Logging is disabled by default when the variable is not set.

For debugging, start Nemo from a terminal with logging enabled:

```bash
nemo -q
NEMO_TAB_RESTORE_LOG=true nemo
```

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

No shortcut configuration is required by default. `Ctrl+W` saves closed-tab history, and `Ctrl+Shift+T` restores the most recently closed tab.

To change shortcuts, edit Nemo / GTK's accelerator file.

The accelerator file location can vary by distribution and Nemo / GTK version. The extension checks these candidates:

```text
$XDG_CONFIG_HOME/nemo/accels/nemo
$XDG_CONFIG_HOME/gtk-3.0/accels/nemo
~/.config/nemo/accels/nemo
~/.gnome2/accels/nemo
~/.config/gtk-3.0/accels/nemo
```

`$XDG_CONFIG_HOME` paths are checked first when the variable is set and non-empty.

Quit Nemo before editing the accelerator file. If Nemo is still running, it may overwrite your changes when it exits.

```bash
nemo -q
```

In the accelerator file, lines starting with `;` are commented out.

In GTK accelerator notation, `<Primary>` usually means the `Ctrl` key.

To explicitly set the restore shortcut, add or edit this line in the accelerator file:

```scheme
(gtk_accel_path "<Actions>/NemoTabRestore/RestoreLastClosedTab" "<Primary><Shift>t")
```

This assigns:

```text
<Primary><Shift>t
```

to this action:

```text
<Actions>/NemoTabRestore/RestoreLastClosedTab
```

The close shortcut follows Nemo's existing close action:

```scheme
(gtk_accel_path "<Actions>/ShellActions/Close" "<Primary>w")
```

This assigns:

```text
<Primary>w
```

to this action:

```text
<Actions>/ShellActions/Close
```

The restore shortcut default, `<Primary><Shift>t`, intentionally follows the browser convention for restoring a closed tab. Nemo also defines `<Primary><Shift>t` as the default accelerator for `<Actions>/DirViewActions/OpenInNewTab`, which opens selected items in new tabs. If you rely on Nemo's original binding, change this extension's restore accelerator to another shortcut in the accel file.

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
NEMO_TAB_RESTORE_LOG=true nemo &
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
- In the current behavior, closed-tab history is shared rather than tracked per window. If multiple Nemo windows are open, restore uses the most recently saved history entry.

## License

MIT License. See [LICENSE](LICENSE).
