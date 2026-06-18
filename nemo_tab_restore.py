# -*- coding: utf-8 -*-
#
# Nemo Tab Restore
#
# Ctrl+W or the configured Nemo close shortcut:
#   Save current tab URI, then let Nemo handle the normal close-tab shortcut.
#
# Ctrl+Shift+T or the configured restore shortcut:
#   Restore the most recently closed tab URI.
#
# History:
#   ~/.local/share/nemo-tab-restore/closed-tabs.jsonl
#   Set NEMO_TAB_RESTORE_HISTORY_MODE=memory to keep history in memory only.
#
# Log:
#   ~/.cache/nemo-tab-restore/nemo-tab-restore.log
#
# Requirements:
#   - nemo-python / python3-nemo
#   - Nemo GI typelib
#     Ubuntu: gir1.2-nemo-3.0
#     openSUSE: typelib-1_0-Nemo-3_0 or equivalent

import os
import sys
import re
import json
import time
import subprocess
import traceback
from urllib.parse import urlparse, unquote

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Nemo", "3.0")

from gi.repository import GObject, Gtk, Gdk, GLib, Nemo


APP_NAME = "nemo-tab-restore"

DATA_DIR = os.path.expanduser("~/.local/share/nemo-tab-restore")
CACHE_DIR = os.path.expanduser("~/.cache/nemo-tab-restore")
HISTORY_FILE = os.path.join(DATA_DIR, "closed-tabs.jsonl")
LOG_FILE = os.path.join(CACHE_DIR, "nemo-tab-restore.log")

MAX_HISTORY_DEFAULT = 100
MAX_HISTORY_MIN = 1
MAX_HISTORY_MAX = 1000
HISTORY_MODE_DEFAULT = "file"

# Logging is disabled by default for normal use.
# Override with:
#   NEMO_TAB_RESTORE_LOG=1 nemo
#   NEMO_TAB_RESTORE_LOG=0 nemo
LOG_ENABLED_DEFAULT = False

def get_accels_file_candidates():
    candidates = []

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home and xdg_config_home.strip():
        xdg_config_home = os.path.expanduser(xdg_config_home.strip())
        candidates.extend([
            os.path.join(xdg_config_home, "nemo", "accels", "nemo"),
            os.path.join(xdg_config_home, "gtk-3.0", "accels", "nemo"),
        ])

    candidates.extend([
        os.path.expanduser("~/.config/nemo/accels/nemo"),
        os.path.expanduser("~/.gnome2/accels/nemo"),
        os.path.expanduser("~/.config/gtk-3.0/accels/nemo"),
    ])

    deduped = []
    seen = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)

    return deduped

# Existing Nemo close action.
CLOSE_ACCEL_PATH = "<Actions>/ShellActions/Close"
CLOSE_ACCEL_DEFAULT = "<Primary>w"

# Extension-owned restore action.
#
# Add this line to the detected Nemo accel file to customize:
#   (gtk_accel_path "<Actions>/NemoTabRestore/RestoreLastClosedTab" "<Primary><Shift>t")
RESTORE_ACCEL_PATH = "<Actions>/NemoTabRestore/RestoreLastClosedTab"
RESTORE_ACCEL_DEFAULT = "<Primary><Shift>t"

_ACCEL_CACHE = {
    "path": None,
    "mtime": None,
    "values": {},
}

# window key -> {"uri": str, "title": str, ...}
_WINDOWS = {}

# widget/page key -> state
_HOOKED_TAB_WIDGETS = set()
_SLOT_URIS = {}
_PENDING_TAB_CLOSES = {}
_PENDING_CONTEXT_TAB_CLOSES = {}
_PENDING_FILE_MENU_CLOSE = None
_RESTORE_AFTER_TAB_CLOSE = {}
_MEMORY_HISTORY = []
_HOOKED_FILE_MENU_ITEMS = set()


def ensure_dirs():
    if get_history_mode() == "file":
        os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)


def log_enabled():
    value = os.environ.get("NEMO_TAB_RESTORE_LOG")
    if value is None:
        return LOG_ENABLED_DEFAULT

    value = value.strip().lower()
    if value in ("1", "true", "yes", "on", "debug"):
        return True
    if value in ("0", "false", "no", "off", ""):
        return False

    return LOG_ENABLED_DEFAULT


def get_history_mode():
    value = os.environ.get("NEMO_TAB_RESTORE_HISTORY_MODE")
    if value is None:
        return HISTORY_MODE_DEFAULT

    value = value.strip().lower()
    if value in ("file", "memory"):
        return value

    return HISTORY_MODE_DEFAULT


def log(message):
    if not log_enabled():
        return

    ensure_dirs()
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "[{}] {}\n".format(stamp, message)

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        try:
            sys.stderr.write(line)
        except Exception:
            pass


def log_exception(context):
    log("EXCEPTION in {}:\n{}".format(context, traceback.format_exc()))


def get_max_history():
    value = os.environ.get("NEMO_TAB_RESTORE_MAX_HISTORY")
    if value is None or value.strip() == "":
        return MAX_HISTORY_DEFAULT

    try:
        n = int(value.strip())
    except Exception:
        return MAX_HISTORY_DEFAULT

    if n < MAX_HISTORY_MIN:
        return MAX_HISTORY_DEFAULT

    if n > MAX_HISTORY_MAX:
        return MAX_HISTORY_MAX

    return n


def now():
    return time.time()


def get_accels_file():
    candidates = get_accels_file_candidates()
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def parse_accels_file():
    """
    Parse Nemo's GTK accel map.

    Active lines win.
    Commented lines are kept as defaults only if there is no active line.
    Nemo/GTK commonly stores default bindings as commented lines.
    """
    accels_file = get_accels_file()

    try:
        st = os.stat(accels_file)
        mtime = st.st_mtime
    except Exception:
        mtime = None

    if (
        _ACCEL_CACHE.get("path") == accels_file
        and _ACCEL_CACHE.get("mtime") == mtime
    ):
        return _ACCEL_CACHE.get("values", {})

    values = {}
    commented_defaults = {}

    try:
        with open(accels_file, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue

                commented = False
                probe = line
                if probe.startswith(";"):
                    commented = True
                    probe = probe[1:].strip()

                m = re.match(
                    r'^\(gtk_accel_path\s+"([^"]+)"\s+"([^"]*)"\s*\)$',
                    probe,
                )
                if not m:
                    continue

                path, accel = m.group(1), m.group(2)

                if commented:
                    commented_defaults.setdefault(path, accel)
                else:
                    values[path] = accel

        for path, accel in commented_defaults.items():
            values.setdefault(path, accel)

    except FileNotFoundError:
        pass
    except Exception:
        log_exception("parse_accels_file")

    _ACCEL_CACHE["path"] = accels_file
    _ACCEL_CACHE["mtime"] = mtime
    _ACCEL_CACHE["values"] = values
    return values


def get_accel_string(path, default_value):
    values = parse_accels_file()
    value = values.get(path)
    if value is None:
        value = default_value
    return value or ""


def parse_accel(accel_string):
    if not accel_string:
        return None

    try:
        keyval, mods = Gtk.accelerator_parse(accel_string)
        if not keyval:
            return None
        return keyval, mods
    except Exception:
        return None


def mods_to_flags(state):
    ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
    shift = bool(state & Gdk.ModifierType.SHIFT_MASK)
    alt = bool(state & Gdk.ModifierType.MOD1_MASK)
    super_ = bool(state & Gdk.ModifierType.SUPER_MASK)
    return ctrl, shift, alt, super_


def event_matches_accel(event, accel_path, default_accel):
    accel_string = get_accel_string(accel_path, default_accel)
    parsed = parse_accel(accel_string)
    if not parsed:
        return False

    accel_keyval, accel_mods = parsed

    try:
        event_keyval = Gdk.keyval_to_lower(event.keyval)
        accel_keyval = Gdk.keyval_to_lower(accel_keyval)
    except Exception:
        event_keyval = event.keyval

    if event_keyval != accel_keyval:
        return False

    ctrl, shift, alt, super_ = mods_to_flags(event.state)

    required_ctrl = bool(accel_mods & Gdk.ModifierType.CONTROL_MASK)
    required_shift = bool(accel_mods & Gdk.ModifierType.SHIFT_MASK)
    required_alt = bool(accel_mods & Gdk.ModifierType.MOD1_MASK)
    required_super = bool(accel_mods & Gdk.ModifierType.SUPER_MASK)

    return (
        ctrl == required_ctrl
        and shift == required_shift
        and alt == required_alt
        and super_ == required_super
    )


def is_close_shortcut(event):
    return event_matches_accel(event, CLOSE_ACCEL_PATH, CLOSE_ACCEL_DEFAULT)


def is_restore_shortcut(event):
    return event_matches_accel(event, RESTORE_ACCEL_PATH, RESTORE_ACCEL_DEFAULT)


def window_key(window):
    """
    Stable key for the underlying C NemoWindow.

    Do not use id(window). PyGObject may create multiple Python wrappers
    for the same underlying NemoWindow, which causes repeated signal
    connection and duplicate key handling.

    repr(window) includes the underlying GObject pointer in tested
    Nemo/PyGObject environments, for example:
      <__gi__.NemoWindow object at 0x... (NemoWindow at 0x...)>
    """
    try:
        r = repr(window)
        m = re.search(
            r"\((?:NemoWindow|GtkWindow|[A-Za-z0-9_]+) at (0x[0-9a-fA-F]+)\)",
            r,
        )
        if m:
            return m.group(1)
    except Exception:
        pass

    try:
        return "hash:{}".format(hash(window))
    except Exception:
        return "id:{}".format(id(window))


def object_key(obj):
    try:
        r = repr(obj)
        m = re.search(r"\(([A-Za-z0-9_]+) at (0x[0-9a-fA-F]+)\)", r)
        if m:
            return "{}:{}".format(m.group(1), m.group(2))
        m = re.search(r" object at (0x[0-9a-fA-F]+)", r)
        if m:
            return "{}:{}".format(obj.__class__.__name__, m.group(1))
    except Exception:
        pass

    try:
        return "hash:{}".format(hash(obj))
    except Exception:
        return "id:{}".format(id(obj))


def notebook_restore_key(notebook):
    notebook_key = object_key(notebook)
    try:
        window = notebook.get_toplevel()
        if window is not None and isinstance(window, Gtk.Window):
            return "{}:{}".format(window_key(window), notebook_key)
    except Exception:
        pass

    return notebook_key


def iter_widget_tree(widget, depth=0, limit=6):
    if depth > limit:
        return

    yield depth, widget

    if not isinstance(widget, Gtk.Container):
        return

    try:
        children = widget.get_children()
    except Exception:
        return

    for child in children:
        yield from iter_widget_tree(child, depth + 1, limit)


def is_close_button_widget(widget):
    try:
        return widget.get_name() == "nemo-tab-close-button"
    except Exception:
        return False


def is_close_button_descendant(widget):
    probe = widget
    while probe is not None:
        if is_close_button_widget(probe):
            return True
        try:
            probe = probe.get_parent()
        except Exception:
            return False
    return False


def tab_label_at_point(notebook, x, y):
    try:
        n_pages = notebook.get_n_pages()
        for index in range(n_pages):
            page = notebook.get_nth_page(index)
            if page is None:
                continue

            tab_label = notebook.get_tab_label(page)
            if tab_label is None:
                continue

            alloc = tab_label.get_allocation()
            if (
                alloc.x <= x < alloc.x + alloc.width
                and alloc.y <= y < alloc.y + alloc.height
            ):
                return page
    except Exception:
        log_exception("tab_label_at_point")

    return None


def menu_item_label(item):
    try:
        label = item.get_label()
        if label:
            return label
    except Exception:
        pass

    labels = []
    try:
        for _depth, widget in iter_widget_tree(item, limit=4):
            if isinstance(widget, Gtk.Label):
                text = widget.get_text()
                if text:
                    labels.append(text)
    except Exception:
        pass

    return " / ".join(labels)


def menu_label_matches(label, expected):
    return label.replace("_", "").strip().lower() == expected


def on_file_close_menu_activate(_item):
    try:
        global _PENDING_FILE_MENU_CLOSE
        item = _PENDING_FILE_MENU_CLOSE
        _PENDING_FILE_MENU_CLOSE = None

        if not item:
            log("file close menu activated but no tab candidate")
            return

        if item.get("at", 0) < now() - 3:
            log("file close menu candidate expired uri={}".format(item.get("uri")))
            return

        push_history(item.get("uri"), title=item.get("title"))
    except Exception:
        log_exception("on_file_close_menu_activate")


def hook_file_menu_widgets(window):
    try:
        for _depth, widget in iter_widget_tree(window, limit=10):
            if not isinstance(widget, Gtk.MenuBar):
                continue

            for child in widget.get_children():
                if not isinstance(child, Gtk.MenuItem):
                    continue

                if not menu_label_matches(menu_item_label(child), "file"):
                    continue

                submenu = child.get_submenu()
                if not isinstance(submenu, Gtk.Menu):
                    continue

                for item in submenu.get_children():
                    if not isinstance(item, Gtk.MenuItem):
                        continue
                    if not menu_label_matches(menu_item_label(item), "close"):
                        continue

                    item_key = object_key(item)
                    if item_key in _HOOKED_FILE_MENU_ITEMS:
                        continue

                    _HOOKED_FILE_MENU_ITEMS.add(item_key)
                    item.connect("activate", on_file_close_menu_activate)
                    log("hooked file close menu item {}".format(item_key))
    except Exception:
        log_exception("hook_file_menu_widgets")


def cleanup_pending_tab_closes():
    cutoff = now() - 5
    for key, item in list(_PENDING_TAB_CLOSES.items()):
        if item.get("at", 0) < cutoff:
            _PENDING_TAB_CLOSES.pop(key, None)


def cleanup_pending_context_tab_closes():
    cutoff = now() - 60
    for key, item in list(_PENDING_CONTEXT_TAB_CLOSES.items()):
        if item.get("at", 0) < cutoff:
            _PENDING_CONTEXT_TAB_CLOSES.pop(key, None)


def remember_current_slots(window, uri, title=""):
    uri = normalize_uri(uri)
    if not uri:
        return

    try:
        for _depth, widget in iter_widget_tree(window):
            if not isinstance(widget, Gtk.Notebook):
                continue

            page_num = widget.get_current_page()
            if page_num < 0:
                continue

            page = widget.get_nth_page(page_num)
            if page is None:
                continue

            _SLOT_URIS[object_key(page)] = {
                "uri": uri,
                "title": title or uri_to_display(uri),
            }
    except Exception:
        log_exception("remember_current_slots")


def mark_current_tabs_as_pending(window, uri):
    uri = normalize_uri(uri)
    if not uri:
        return

    try:
        for _depth, widget in iter_widget_tree(window):
            if not isinstance(widget, Gtk.Notebook):
                continue

            page_num = widget.get_current_page()
            if page_num < 0:
                continue

            page = widget.get_nth_page(page_num)
            if page is None:
                continue

            page_key = object_key(page)
            item = _SLOT_URIS.get(page_key)
            if item and normalize_uri(item.get("uri")) == uri:
                _PENDING_TAB_CLOSES[page_key] = {"at": now()}
    except Exception:
        log_exception("mark_current_tabs_as_pending")


def restore_active_page_after_tab_close(notebook, removed_page):
    try:
        notebook_key = notebook_restore_key(notebook)
        restore = _RESTORE_AFTER_TAB_CLOSE.get(notebook_key)
        if not restore or restore.get("target_key") != object_key(removed_page):
            return

        restore_page = restore.get("page")
        restore_key = restore.get("page_key")

        def do_restore():
            try:
                n_pages = notebook.get_n_pages()
                for index in range(n_pages):
                    page = notebook.get_nth_page(index)
                    if page is restore_page or object_key(page) == restore_key:
                        notebook.set_current_page(index)
                        log("restored active tab after tab close page={}".format(index))
                        return False
            except Exception:
                log_exception("restore active tab")
            finally:
                _RESTORE_AFTER_TAB_CLOSE.pop(notebook_key, None)

            return False

        GLib.idle_add(do_restore)
    except Exception:
        log_exception("restore_active_page_after_tab_close")


def capture_tab_history_item(notebook, page, restore_mode):
    try:
        if page is None:
            return None, None

        page_num = notebook.page_num(page)
        if page_num < 0:
            return None, None

        page_key = object_key(page)
        current_page_num = notebook.get_current_page()
        current_page = notebook.get_nth_page(current_page_num) if current_page_num >= 0 else None

        item = _SLOT_URIS.get(page_key)

        if not item and current_page is not None and current_page is not page:
            # Nemo exposes the current location through get_widget(), so an
            # unseen inactive tab needs to become current once before closing.
            if restore_mode == "after-close":
                _RESTORE_AFTER_TAB_CLOSE[notebook_restore_key(notebook)] = {
                    "target_key": page_key,
                    "page": current_page,
                    "page_key": object_key(current_page),
                }

            notebook.set_current_page(page_num)
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)

            item = _SLOT_URIS.get(page_key)

            if restore_mode == "immediate":
                notebook.set_current_page(current_page_num)
                while Gtk.events_pending():
                    Gtk.main_iteration_do(False)

        return page_key, item

    except Exception:
        log_exception("capture_tab_history_item")
        return None, None


def prepare_tab_close(notebook, page, event, event_widget=None):
    try:
        button = getattr(event, "button", None)
        close_button_press = (
            button == 1
            and event_widget is not None
            and is_close_button_descendant(event_widget)
        )
        if button != 2 and not close_button_press:
            return

        cleanup_pending_tab_closes()
        page_key, item = capture_tab_history_item(notebook, page, "after-close")
        if not page_key or page_key in _PENDING_TAB_CLOSES:
            return

        if not item:
            return

        uri = item.get("uri")
        title = item.get("title") or uri_to_display(uri)
        if push_history(uri, title=title):
            _PENDING_TAB_CLOSES[page_key] = {"at": now(), "uri": uri}

    except Exception:
        log_exception("prepare_tab_close")


def prepare_context_tab_close(notebook, page, event):
    try:
        if getattr(event, "button", None) != 3:
            return

        cleanup_pending_context_tab_closes()
        page_key, item = capture_tab_history_item(notebook, page, "immediate")
        if not page_key or not item:
            return

        uri = item.get("uri")
        if not normalize_uri(uri):
            return

        _PENDING_CONTEXT_TAB_CLOSES[page_key] = {
            "at": now(),
            "notebook": notebook_restore_key(notebook),
            "uri": uri,
            "title": uri_to_title(uri),
        }
        log("context close candidate uri={} title={!r}".format(
            uri,
            _PENDING_CONTEXT_TAB_CLOSES[page_key]["title"],
        ))
    except Exception:
        log_exception("prepare_context_tab_close")


def on_notebook_button_press(notebook, event):
    try:
        button = getattr(event, "button", None)
        if button == 3:
            page = tab_label_at_point(
                notebook,
                getattr(event, "x", -1),
                getattr(event, "y", -1),
            )
            prepare_context_tab_close(notebook, page, event)

        if button != 2:
            return False

        page = tab_label_at_point(
            notebook,
            getattr(event, "x", -1),
            getattr(event, "y", -1),
        )
        prepare_tab_close(notebook, page, event, event_widget=notebook)
    except Exception:
        log_exception("on_notebook_button_press")

    return False


def on_tab_widget_button_press(widget, event, notebook, page):
    try:
        prepare_context_tab_close(notebook, page, event)
        prepare_tab_close(notebook, page, event, event_widget=widget)
    except Exception:
        log_exception("on_tab_widget_button_press")

    return False


def on_notebook_page_removed(notebook, page, _page_num):
    global _PENDING_FILE_MENU_CLOSE

    try:
        page_key = object_key(page)
        context_item = _PENDING_CONTEXT_TAB_CLOSES.pop(page_key, None)
        if (
            context_item
            and page_key not in _PENDING_TAB_CLOSES
            and context_item.get("notebook") == notebook_restore_key(notebook)
        ):
            push_history(context_item.get("uri"), title=context_item.get("title"))
        elif page_key not in _PENDING_TAB_CLOSES:
            item = _SLOT_URIS.get(page_key)
            if item:
                uri = normalize_uri(item.get("uri"))
                if uri:
                    _PENDING_FILE_MENU_CLOSE = {
                        "at": now(),
                        "uri": uri,
                        "title": item.get("title") or uri_to_title(uri),
                    }
        _PENDING_TAB_CLOSES.pop(page_key, None)
        _SLOT_URIS.pop(page_key, None)
        restore_active_page_after_tab_close(notebook, page)
    except Exception:
        log_exception("on_notebook_page_removed")


def hook_tab_label_tree(notebook, page, index):
    try:
        tab_label = notebook.get_tab_label(page)
        if tab_label is None:
            return

        hooked = 0
        for _depth, widget in iter_widget_tree(tab_label, limit=3):
            key = object_key(widget)
            if key in _HOOKED_TAB_WIDGETS:
                continue
            _HOOKED_TAB_WIDGETS.add(key)
            widget.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            widget.connect("button-press-event", on_tab_widget_button_press, notebook, page)
            hooked += 1

        if hooked:
            log("hooked tab label index={} page={} widgets={}".format(index, object_key(page), hooked))
    except Exception:
        log_exception("hook_tab_label_tree")


def hook_notebook(notebook):
    try:
        notebook_key = object_key(notebook)
        if notebook_key not in _HOOKED_TAB_WIDGETS:
            _HOOKED_TAB_WIDGETS.add(notebook_key)
            notebook.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            notebook.connect("button-press-event", on_notebook_button_press)
            notebook.connect("page-removed", on_notebook_page_removed)
            log("hooked notebook {}".format(notebook_key))

        n_pages = notebook.get_n_pages()
        for index in range(n_pages):
            page = notebook.get_nth_page(index)
            if page is not None:
                hook_tab_label_tree(notebook, page, index)
    except Exception:
        log_exception("hook_notebook")


def hook_tab_widgets(window):
    try:
        for _depth, widget in iter_widget_tree(window):
            if isinstance(widget, Gtk.Notebook):
                hook_notebook(widget)
    except Exception:
        log_exception("hook_tab_widgets")


def forget_window_tab_state(window):
    try:
        for _depth, widget in iter_widget_tree(window):
            if not isinstance(widget, Gtk.Notebook):
                continue

            notebook_key = notebook_restore_key(widget)
            _RESTORE_AFTER_TAB_CLOSE.pop(notebook_key, None)

            n_pages = widget.get_n_pages()
            for index in range(n_pages):
                page = widget.get_nth_page(index)
                if page is None:
                    continue

                page_key = object_key(page)
                _SLOT_URIS.pop(page_key, None)
                _PENDING_TAB_CLOSES.pop(page_key, None)
                _PENDING_CONTEXT_TAB_CLOSES.pop(page_key, None)
    except Exception:
        log_exception("forget_window_tab_state")


def uri_to_display(uri):
    if not uri:
        return ""
    try:
        parsed = urlparse(uri)
        if parsed.scheme == "file":
            return unquote(parsed.path)
    except Exception:
        pass
    return uri


def uri_to_title(uri):
    display = uri_to_display(uri)
    if not display:
        return ""

    try:
        parsed = urlparse(uri)
        if parsed.scheme == "file":
            path = unquote(parsed.path).rstrip(os.sep)
            base = os.path.basename(path)
            if base:
                return base
    except Exception:
        pass

    return display


def file_uri_exists(uri):
    """
    Return True if:
      - URI is not file://
      - file:// path exists

    For non-file URI, Nemo may still know how to open it.
    """
    try:
        parsed = urlparse(uri)
        if parsed.scheme != "file":
            return True
        path = unquote(parsed.path)
        return os.path.exists(path)
    except Exception:
        return True


def normalize_uri(uri):
    if not uri:
        return None
    uri = str(uri).strip()
    if not uri:
        return None
    return uri


def read_history():
    if get_history_mode() == "memory":
        return list(_MEMORY_HISTORY)

    ensure_dirs()
    items = []

    if not os.path.exists(HISTORY_FILE):
        return items

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    item = json.loads(line)
                except Exception:
                    continue

                uri = normalize_uri(item.get("uri"))
                if not uri:
                    continue

                items.append({
                    "uri": uri,
                    "title": item.get("title") or "",
                    "closed_at": item.get("closed_at") or 0,
                })
    except Exception:
        log_exception("read_history")
        return []

    return items


def write_history(items):
    items = items[-get_max_history():]

    if get_history_mode() == "memory":
        _MEMORY_HISTORY[:] = items
        return

    ensure_dirs()

    tmp = HISTORY_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(tmp, HISTORY_FILE)
    except Exception:
        log_exception("write_history")
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def push_history(uri, title=""):
    uri = normalize_uri(uri)
    if not uri:
        return False

    items = read_history()

    item = {
        "uri": uri,
        "title": title or uri_to_display(uri),
        "closed_at": int(now()),
    }

    items.append(item)
    write_history(items)

    log("pushed uri={} title={!r}".format(uri, item["title"]))
    return True


def pop_history_existing():
    """
    Pop from the tail.
    If file:// path no longer exists, discard and continue.
    """
    items = read_history()

    while items:
        item = items.pop()
        uri = normalize_uri(item.get("uri"))
        if not uri:
            continue

        if not file_uri_exists(uri):
            log("discard missing uri={}".format(uri))
            continue

        write_history(items)
        log("popped uri={}".format(uri))
        return item

    write_history([])
    return None


def get_window_title(window):
    try:
        title = window.get_title()
        if title:
            return str(title)
    except Exception:
        pass
    return ""


def open_uri_in_existing_window(uri):
    uri = normalize_uri(uri)
    if not uri:
        return False

    try:
        subprocess.Popen(
            ["nemo", "--existing-window", "--tabs", uri],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        log("restore launched uri={}".format(uri))
        return True
    except Exception:
        log_exception("open_uri_in_existing_window")
        return False


def on_key_press(window, event):
    """
    Close shortcut:
      Save URI, return False so Nemo closes the tab normally.

    Restore shortcut:
      Restore URI, return True so Nemo does not also process it.
    """
    try:
        wid = window_key(window)
        info = _WINDOWS.get(wid, {})
        uri = info.get("uri")
        title = info.get("title") or get_window_title(window)

        if is_close_shortcut(event):
            if uri:
                if push_history(uri, title=title):
                    mark_current_tabs_as_pending(window, uri)
            else:
                log("close shortcut observed but no URI known")

            # Let Nemo handle standard close-tab.
            return False

        if is_restore_shortcut(event):
            item = pop_history_existing()
            if not item:
                log("restore requested but history is empty")
                return True

            open_uri_in_existing_window(item["uri"])

            # This shortcut is handled by us.
            return True

    except Exception:
        log_exception("on_key_press")

    return False


def on_window_destroy(window):
    try:
        wid = window_key(window)
        forget_window_tab_state(window)
        _WINDOWS.pop(wid, None)
        log("window destroy wid={}".format(wid))
    except Exception:
        log_exception("on_window_destroy")


def ensure_window_hooked(window, uri=None):
    try:
        wid = window_key(window)
        title = get_window_title(window)

        if wid not in _WINDOWS:
            _WINDOWS[wid] = {
                "uri": normalize_uri(uri),
                "title": title,
                "key_handler_id": None,
                "destroy_handler_id": None,
            }

            key_id = window.connect("key-press-event", on_key_press)
            destroy_id = window.connect("destroy", on_window_destroy)

            _WINDOWS[wid]["key_handler_id"] = key_id
            _WINDOWS[wid]["destroy_handler_id"] = destroy_id

            log("hooked window wid={} uri={} title={!r}".format(wid, uri, title))
        elif uri:
            old_uri = _WINDOWS[wid].get("uri")
            new_uri = normalize_uri(uri)
            if new_uri and old_uri != new_uri:
                _WINDOWS[wid]["uri"] = new_uri
                log("location change wid={} old={} new={}".format(wid, old_uri, new_uri))

        if title:
            _WINDOWS[wid]["title"] = title

        remember_current_slots(window, _WINDOWS[wid].get("uri"), _WINDOWS[wid].get("title", ""))
        hook_tab_widgets(window)
        hook_file_menu_widgets(window)

    except Exception:
        log_exception("ensure_window_hooked")


class NemoTabRestore(GObject.GObject,
                     Nemo.LocationWidgetProvider,
                     Nemo.MenuProvider):
    def __init__(self):
        GObject.GObject.__init__(self)
        ensure_dirs()

        log("loaded {} python={} pid={} session={}".format(
            APP_NAME,
            sys.version.split()[0],
            os.getpid(),
            os.environ.get("XDG_SESSION_TYPE", ""),
        ))
        log("accels file -> {}".format(get_accels_file()))
        log("accel close {} -> {!r}".format(
            CLOSE_ACCEL_PATH,
            get_accel_string(CLOSE_ACCEL_PATH, CLOSE_ACCEL_DEFAULT),
        ))
        log("accel restore {} -> {!r}".format(
            RESTORE_ACCEL_PATH,
            get_accel_string(RESTORE_ACCEL_PATH, RESTORE_ACCEL_DEFAULT),
        ))
        log("history mode -> {}".format(get_history_mode()))
        log("max history -> {}".format(get_max_history()))

    def get_widget(self, uri, window):
        """
        Called by Nemo for the current location.
        Used only to track URI/window.
        """
        try:
            ensure_window_hooked(window, uri)
        except Exception:
            log_exception("get_widget")

        # Invisible widget.
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.set_size_request(0, 0)
        box.set_no_show_all(True)
        box.hide()
        return box

    def get_background_items(self, window, file):
        """
        Also hook via background menu path.
        Adds a small utility menu item for manual restore.
        """
        try:
            uri = None
            try:
                if file is not None:
                    uri = file.get_uri()
            except Exception:
                pass

            ensure_window_hooked(window, uri)

            restore_item = Nemo.MenuItem(
                name="NemoTabRestore::restore_last_closed_tab",
                label="Restore Last Closed Tab",
                tip="Restore the most recently closed Nemo tab",
                icon="edit-undo",
            )

            def on_restore(_item):
                try:
                    item = pop_history_existing()
                    if item:
                        open_uri_in_existing_window(item["uri"])
                    else:
                        log("menu restore requested but history is empty")
                except Exception:
                    log_exception("menu restore")

            restore_item.connect("activate", on_restore)
            return [restore_item]

        except Exception:
            log_exception("get_background_items")
            return []

    def get_file_items(self, window, files):
        return []
