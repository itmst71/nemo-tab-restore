# Nemo Tab Restore

[日本語版](README.ja.md)

Nemo Tab Restore is a `nemo-python` extension that adds browser-like closed-tab restoration to the Nemo file manager.

Tabs closed with `Ctrl+W`, mouse actions, and similar close operations can be restored with `Ctrl+Shift+T`.

## Features

- Saves history for tabs closed with `Ctrl+W`
- Saves history for tabs closed with mouse actions or the File menu
- Restores the most recently closed tab with `Ctrl+Shift+T`
- Supports changing shortcuts
- Supports configuration through a configuration file or environment variables
- Supports shared, per-window, or hybrid restore history
- Supports file-backed or in-memory history

## Requirements

In addition to Nemo itself, this extension needs the Python bindings that let Nemo load Python extensions, plus the GI / PyGObject packages used by those bindings. Some distributions pull part of this stack through the Nemo package itself, so the number of extra packages may vary by environment.

### Linux Mint

On Linux Mint 22.3 Cinnamon, this extension has been confirmed to work without installing additional packages. In the tested default environment, `python-nemo`, `gir1.2-nemo-3.0`, `python3-gi`, and `python3-gi-cairo` were already available.

Try the install steps first. If Nemo does not load the extension after restarting, check the related packages:

```bash
dpkg -l python-nemo gir1.2-nemo-3.0 python3-gi python3-gi-cairo
```

### Ubuntu family

The following package names are confirmed on Ubuntu 24.04-family systems:

```bash
sudo apt install nemo-python gir1.2-nemo-3.0 python3-gi python3-gi-cairo
```

On Ubuntu-family releases, package names may vary. If installation fails, check the available package names with `apt search nemo-python` and `apt search gir1.2-nemo`.

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

Install this extension file into Nemo's Python extension directory.

To install manually:

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

Remove the installed extension file.

To remove it manually:

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

The extension saves the closed tab URI to history for these close operations:

- `Ctrl+W`
- tab close button
- middle-click on a tab
- tab context menu close
- File menu Close

After saving the URI, Nemo closes the tab normally.

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

This file is not used when the history mode is `memory`.

Log file:

```text
~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

Configuration file:

```text
~/.config/nemo-tab-restore/config.env
```

## Configuration

Configuration is done with environment variables or a configuration file. Environment variables are useful for temporary overrides. For persistent settings, use the configuration file so the values do not depend on how Nemo was started.

### Priority

Settings listed higher take precedence. For example, if the configuration file and an environment variable specify different values, the environment variable value is used.

```text
environment variables
configuration file
Nemo / GTK accelerator file (shortcuts only)
defaults
```

### Environment Variables

Environment variables are useful when starting Nemo from a terminal to try temporary settings.

#### `NEMO_TAB_RESTORE_RESTORE_SHORTCUT`

Sets this extension's restore shortcut.

```env
NEMO_TAB_RESTORE_RESTORE_SHORTCUT=Ctrl+Shift+T
```

The default is `Ctrl+Shift+T`. To use a different shortcut, specify a value such as `Ctrl+Shift+Y`.

If you assign the same shortcut as a built-in Nemo action, the built-in action may be hidden. To adjust Nemo's built-in shortcuts too, see the [Shortcuts](#shortcuts) section below.

#### `NEMO_TAB_RESTORE_MAX_HISTORY`

Sets the maximum number of closed-tab history entries to keep.

```env
NEMO_TAB_RESTORE_MAX_HISTORY=100
```

The default is `100`, and the maximum is `1000`.

#### `NEMO_TAB_RESTORE_HISTORY_MODE`

Sets where closed-tab history is stored.

```env
NEMO_TAB_RESTORE_HISTORY_MODE=file
NEMO_TAB_RESTORE_HISTORY_MODE=memory
```

The default is `file`. Closed-tab history is saved to `~/.local/share/nemo-tab-restore/closed-tabs.jsonl`.

When set to `memory`, history is kept only in memory while Nemo is running. It is lost when Nemo quits completely, and the history file is not read or written.

#### `NEMO_TAB_RESTORE_HISTORY_SCOPE`

Sets how restore history is handled across Nemo windows.

```env
NEMO_TAB_RESTORE_HISTORY_SCOPE=shared
NEMO_TAB_RESTORE_HISTORY_SCOPE=window
NEMO_TAB_RESTORE_HISTORY_SCOPE=hybrid
```

The default is `shared`.

`shared` uses one restore history across all Nemo windows.

`window` restores only tabs closed in the current window.

`hybrid` prefers the current window's history. If there is nothing to restore for the current window, history from closed windows and old-format history entries is also considered.

#### `NEMO_TAB_RESTORE_LOG`

Configures debug logging.

```env
NEMO_TAB_RESTORE_LOG=true
NEMO_TAB_RESTORE_LOG=false
```

Use `true` or `false` in normal use. Logging is disabled by default when the variable is not set.

#### Temporary Startup Examples

When starting Nemo from a terminal, place environment variables before the command to apply temporary settings:

```bash
NEMO_TAB_RESTORE_LOG=true nemo
```

You can also set multiple environment variables at once:

```bash
NEMO_TAB_RESTORE_LOG=true NEMO_TAB_RESTORE_MAX_HISTORY=300 nemo
```

### Configuration File

The configuration file uses the same names and values as the environment variables above, written as `KEY=value`.

If the configuration file does not exist, the extension creates it the first time it is loaded. All settings are created as commented-out examples. Uncomment only the settings you want to override.

```text
~/.config/nemo-tab-restore/config.env
```

When new settings are added in a newer version, existing configuration files are not updated automatically. To regenerate the latest sample, save any settings you still need, delete `~/.config/nemo-tab-restore/config.env`, and restart Nemo.

Example:

```env
NEMO_TAB_RESTORE_MAX_HISTORY=300
NEMO_TAB_RESTORE_HISTORY_MODE=memory
NEMO_TAB_RESTORE_HISTORY_SCOPE=hybrid
NEMO_TAB_RESTORE_LOG=true
NEMO_TAB_RESTORE_RESTORE_SHORTCUT=Ctrl+Shift+Y
```

The configuration file uses a `.env`-like format. It is not a full shell script.

Supported format:

```text
KEY=value
# comment
blank lines
```

`export`, variable expansion, and complex shell quoting or escaping are not supported.

## Shortcuts

No shortcut configuration is required by default. `Ctrl+W` saves closed-tab history, and `Ctrl+Shift+T` restores the most recently closed tab.

This extension uses `Ctrl+Shift+T` to match the browser convention for restoring a closed tab. Nemo itself also uses `Ctrl+Shift+T` by default for `<Actions>/DirViewActions/OpenInNewTab`, which opens selected items in new tabs.

To change only this extension's restore shortcut, you can also use an environment variable or the configuration file. See [`NEMO_TAB_RESTORE_RESTORE_SHORTCUT`](#nemo_tab_restore_restore_shortcut) for details.

To also change Nemo's built-in shortcuts, such as Open in New Tab, you need to edit Nemo / GTK's accelerator file.

If the accelerator file does not exist, you can create this path manually. See [Behavior details](#behavior-details) for other candidate paths.

```text
~/.config/nemo/accels/nemo
```

Quit Nemo before editing the accelerator file. If Nemo is still running, it may overwrite your changes when it exits.

```bash
nemo -q
```

In GTK accelerator notation, `<Primary>` usually means the `Ctrl` key.

Example: change tab restore to `Ctrl+Shift+Y` through the accelerator file:

```scheme
(gtk_accel_path "<Actions>/NemoTabRestore/RestoreLastClosedTab" "<Primary><Shift>y")
```

Example: change Nemo's built-in Open in New Tab shortcut to `Ctrl+Shift+Y`:

```scheme
(gtk_accel_path "<Actions>/DirViewActions/OpenInNewTab" "<Primary><Shift>y")
```

The close shortcut follows Nemo's existing close action (`<Actions>/ShellActions/Close`). Normally, you do not need to change it.

## Syntax Check

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

- This extension restores closed tabs individually when requested. It does not manage Nemo sessions or restore the tabs that were open when Nemo last exited.
- Tracking tab closes from mouse actions can depend on the Nemo version, theme, and GTK widget structure. If it does not work in a given environment, keyboard shortcut closes are still tracked.
- When closing an inactive tab with a mouse action or opening its context menu, the extension may briefly switch to that tab to capture its URI. It switches back to the previously active tab after capturing the URI.
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
- When closing an inactive tab with a mouse action before its URI is known, the extension briefly switches to that tab to capture the URI, then returns to the previously active tab after the close.
- With `NEMO_TAB_RESTORE_HISTORY_SCOPE=shared`, closed-tab history is shared rather than tracked per window.
- When `NEMO_TAB_RESTORE_HISTORY_SCOPE=window` is combined with `NEMO_TAB_RESTORE_HISTORY_MODE=file`, history from old windows remains in the history file but is not restored from the current window. If needed, switch to `shared` or `hybrid` to make those entries eligible for restore.
- With `NEMO_TAB_RESTORE_HISTORY_SCOPE=hybrid`, history from other currently open Nemo windows is not used as fallback restore history.

The accelerator file location can vary by distribution and Nemo / GTK version. The extension checks these candidates:

```text
$XDG_CONFIG_HOME/nemo/accels/nemo
$XDG_CONFIG_HOME/gtk-3.0/accels/nemo
~/.config/nemo/accels/nemo
~/.gnome2/accels/nemo
~/.config/gtk-3.0/accels/nemo
```

`$XDG_CONFIG_HOME` paths are checked first when the variable is set and non-empty.

## License

MIT License. See [LICENSE](LICENSE).
