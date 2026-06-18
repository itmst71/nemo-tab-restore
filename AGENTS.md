# AGENTS.md

## Project

This repository contains a `nemo-python` extension named **Nemo Tab Restore**.

The goal is to add browser-like closed-tab restoration to the Nemo file manager:

* close shortcut:

  * save the current tab URI to history
  * return `False` so Nemo handles the normal close-tab action
* restore shortcut:

  * pop the last closed URI from history
  * open it with `nemo --existing-window --tabs URI`
  * return `True`

This project targets practical local use first, then public release.

## Language and response style

* Use Japanese for explanations to the project owner unless explicitly asked otherwise.
* Keep explanations technical but concise.
* When proposing code changes, explain the behavioral effect first.
* Do not make speculative rewrites when the source shape is uncertain.
* If a patch cannot find the expected code block, stop and provide an inspection command or script instead of guessing.

## Hard rules

### Do not reintroduce debounce

Do not add debounce to either close or restore shortcuts.

Current policy:

```text
Ctrl+W:
  no debounce

Ctrl+Shift+T:
  no debounce
```

Rationale:

* The old duplicate event problem was caused by multiple signal handlers attached to the same underlying NemoWindow.
* Debounce caused legitimate fast repeated close/restore operations to be dropped.
* Browser-like behavior is preferred: each key press should count.

### Do not suppress duplicate consecutive URIs

Do not add logic like this:

```python
if items and items[-1].get("uri") == uri:
    return False
```

The same folder can legitimately be open in multiple tabs. If the user closes duplicate URI tabs, restoring multiple duplicate URI tabs should be possible.

### Do not replace `window_key()` with `id(window)`

PyGObject can produce multiple Python wrappers for the same underlying C NemoWindow. `id(window)` can therefore cause repeated signal connections.

Use the existing `repr(window)` pointer parsing strategy unless there is strong new evidence and a tested migration plan.

### Do not use `__gpointer__` / `__pointer__` for window identity

This was tested and rejected.

Observed bad log pattern:

```text
wid=__gpointer__:<capsule object NULL at 0x...>
wid=__gpointer__:<capsule object NULL at 0x...>
wid=__gpointer__:<capsule object NULL at 0x...>
```

It caused multiple hook entries for what should be the same window.

### Do not use GObject qdata / set_data / get_data for state

This was tested and rejected.

`window.set_data()` / `window.get_data()` probe produced repeated exceptions in the target environment.

Do not reintroduce this direction unless the project owner explicitly asks for a new isolated probe.

### Do not depend on xdotool

This extension is intended to work on Wayland and X11.

Do not use:

```text
xdotool
wmctrl
X11-only active window control
```

### Prefer distribution Python for GI

Nemo Python extensions use GI / PyGObject from the distribution packages.

If Python conflicts with `gi`, prefer documenting or testing with the distribution Python, such as `/usr/bin/python3`, instead of assuming any specific third-party Python environment.

## Current important implementation details

### Files

Main extension:

```text
nemo_tab_restore.py
```

Install location:

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

### Environment variables

Logging:

```text
NEMO_TAB_RESTORE_LOG=1
NEMO_TAB_RESTORE_LOG=0
```

History size:

```text
NEMO_TAB_RESTORE_MAX_HISTORY=300
```

Current expected constants:

```python
MAX_HISTORY_DEFAULT = 100
MAX_HISTORY_MIN = 1
MAX_HISTORY_MAX = 1000
LOG_ENABLED_DEFAULT = False
```

### Shortcut handling

Close action path:

```text
<Actions>/ShellActions/Close
```

Close default:

```text
<Primary>w
```

Restore action path:

```text
<Actions>/NemoTabRestore/RestoreLastClosedTab
```

Restore default:

```text
<Primary><Shift>t
```

Accel files checked:

```text
$XDG_CONFIG_HOME/nemo/accels/nemo
$XDG_CONFIG_HOME/gtk-3.0/accels/nemo
~/.config/nemo/accels/nemo
~/.gnome2/accels/nemo
~/.config/gtk-3.0/accels/nemo
```

The `$XDG_CONFIG_HOME` candidates are used only when the variable is set and non-empty.

### Window identity

Use this strategy:

```python
repr(window)
```

Parse the underlying C-side pointer from a string like:

```text
<__gi__.NemoWindow object at 0x... (NemoWindow at 0x...)>
```

The `window_key()` result should look like:

```text
0x58f1cd155b60
```

Bad result examples:

```text
__gpointer__:<capsule object NULL at 0x...>
id:...
```

`hash:` and `id:` fallback may remain as last-resort fallback only, but they must not be the normal path.

## Testing commands

### Syntax check

Use the system Python when possible.

```bash
/usr/bin/python3 -m py_compile nemo_tab_restore.py
```

If testing the installed file:

```bash
/usr/bin/python3 -m py_compile ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

### Install locally

```bash
mkdir -p ~/.local/share/nemo-python/extensions
cp nemo_tab_restore.py ~/.local/share/nemo-python/extensions/nemo_tab_restore.py
```

### Restart Nemo with logs

```bash
nemo -q
sleep 1
rm -f ~/.cache/nemo-tab-restore/nemo-tab-restore.log
NEMO_TAB_RESTORE_LOG=1 nemo &
```

### Inspect logs

```bash
tail -f ~/.cache/nemo-tab-restore/nemo-tab-restore.log
```

Expected window hook:

```text
hooked window wid=0x... uri=file:///... title='Loading...'
```

Bad window hook:

```text
hooked window wid=__gpointer__:<capsule object NULL at 0x...>
```

### Check no rejected code remains

```bash
grep -n "__gpointer__\|__pointer__\|qdata\|set_data\|get_data\|shortcut_debounced\|DEBOUNCE\|skip duplicate\|duplicate top" nemo_tab_restore.py
```

Expected result:

```text
no output
```

### Check expected constants

```bash
grep -n "MAX_HISTORY_DEFAULT\|MAX_HISTORY_MIN\|MAX_HISTORY_MAX\|LOG_ENABLED_DEFAULT" nemo_tab_restore.py
```

Expected:

```text
MAX_HISTORY_DEFAULT = 100
MAX_HISTORY_MIN = 1
MAX_HISTORY_MAX = 1000
LOG_ENABLED_DEFAULT = False
```

## Preferred development workflow

1. Read this `AGENTS.md`.
2. Inspect current `nemo_tab_restore.py`.
3. Make the smallest change that satisfies the requested task.
4. Preserve behavior unless the user explicitly asks for behavior changes.
5. Run syntax checks.
6. Provide install/restart/test commands.
7. Explain exactly what changed.

## Patch style

When giving patches in chat, prefer copyable shell heredocs or small Python patchers.

Good:

```bash
python3 - <<'PY'
from pathlib import Path
p = Path("nemo_tab_restore.py")
s = p.read_text(encoding="utf-8")
# patch here
p.write_text(s, encoding="utf-8")
PY
```

Avoid providing only a downloadable file.

## Suggested repository structure

```text
nemo-tab-restore/
  AGENTS.md
  README.md
  README.ja.md
  LICENSE
  .gitignore
  nemo_tab_restore.py
```

Local private notes may live under ignored `.local/`, for example `.local/HANDOFF.md`.
Optional helper scripts may be added under `scripts/` later if they stay behavior-preserving.

## Public release requirements

Before public release, add or verify:

* `README.md`
* `README.ja.md`
* `LICENSE`
* `.gitignore`
* known limitations
* supported distributions, including Linux Mint / Ubuntu family
* dependencies
* environment variables
* troubleshooting section for Python / GI issues

Optional before public release:

* install script
* uninstall script

## Known limitations to preserve in README

* These close operations are tracked:

  * keyboard close shortcut
  * tab close button
  * middle-click tab close
* Tab context menu close is not tracked.
* Full open-tab enumeration is not implemented.
* This is a Nemo extension, not Nautilus or Caja.
* Wayland is supported because no X11 automation tool is used.

## Behavioral invariants

These should remain true after any refactor:

```text
Ctrl+W once:
  one history push
  Nemo closes tab normally

Ctrl+W repeatedly:
  one history push per actual key press

Ctrl+Shift+T once:
  one history pop
  one restore launch

Ctrl+Shift+T repeatedly:
  one history pop/restore per actual key press

same URI closed twice:
  two history entries

missing file:// URI on restore:
  discard it and try older history

non-file URI:
  do not require local path existence
```

## Current rejected ideas

Rejected after testing:

```text
debounce for shortcut handling
id(window)
__gpointer__ / __pointer__
GObject qdata / set_data / get_data
duplicate URI suppression
xdotool-based implementation
```
