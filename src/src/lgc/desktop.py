"""Integracja z pulpitem: licznik na ikonie w docku, autostart, ikona jasna/ciemna (także przy zamkniętej
aplikacji – usługa w autostarcie sesji, patrz watch())."""
import os
import shutil
import sys

from gi.repository import Gio, GLib

from . import APP_ID, PKG_NAME, paths

HOME = os.path.expanduser("~")
USER_ICON = os.path.join(GLib.get_user_data_dir(), "icons/hicolor/scalable/apps", APP_ID + ".svg")
USER_DESKTOP = os.path.join(GLib.get_user_data_dir(), "applications", APP_ID + ".desktop")
SYSTEM_DESKTOP = os.path.join("/usr/share/applications", APP_ID + ".desktop")
AUTOSTART = os.path.join(GLib.get_user_config_dir(), "autostart", APP_ID + ".desktop")


# ------------------------------------------------------------------ licznik w docku
class LauncherBadge:
    """Licznik nieprzeczytanych na ikonie w Ubuntu Dock (com.canonical.Unity.LauncherEntry)."""

    def __init__(self):
        try:
            self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error:
            self.bus = None
        self.count = -1

    def set(self, count):
        if self.bus is None or count == self.count:
            return
        self.count = count
        try:
            self.bus.emit_signal(None, "/com/canonical/unity/launcherentry/%d" % abs(hash(APP_ID)),
                                 "com.canonical.Unity.LauncherEntry", "Update",
                                 GLib.Variant("(sa{sv})", ("application://%s.desktop" % APP_ID, {
                                     "count": GLib.Variant("x", count),
                                     "count-visible": GLib.Variant("b", count > 0)})))
        except GLib.Error:
            pass


# ------------------------------------------------------------------ autostart aplikacji (w tle)
def set_autostart(on):
    if on:
        os.makedirs(os.path.dirname(AUTOSTART), exist_ok=True)
        with open(AUTOSTART, "w", encoding="utf-8") as f:
            f.write("[Desktop Entry]\nType=Application\nName=Linux Google Chat\n"
                    f"Exec={PKG_NAME} --hidden\nIcon={APP_ID}\nX-GNOME-Autostart-enabled=true\n"
                    "X-GNOME-Autostart-Delay=8\n")
    elif os.path.exists(AUTOSTART):
        os.remove(AUTOSTART)


# ------------------------------------------------------------------ ikona jasna / ciemna
def system_dark():
    try:
        src = Gio.SettingsSchemaSource.get_default()
        if src and src.lookup("org.gnome.desktop.interface", True):
            s = Gio.Settings.new("org.gnome.desktop.interface")
            if s.get_string("color-scheme") == "prefer-dark":
                return True
            return "dark" in s.get_string("gtk-theme").lower() and s.get_string("color-scheme") == "default"
    except Exception:  # noqa: BLE001
        pass
    return False


def tray_icon_name(dark, unread):
    return "lgc-tray-%s%s" % ("dark" if dark else "light", "-unread" if unread else "")


def _write_if_changed(path, data):
    try:
        with open(path, "rb") as f:
            if f.read() == data:
                return False
    except OSError:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "wb") as f:
        f.write(data)
    os.replace(path + ".tmp", path)
    return True


def apply_icon(dark=None):
    """Podmienia ikonę w menu aplikacji i docku (kopia użytkownika pliku .desktop wskazuje na wariant)."""
    if not os.path.exists(SYSTEM_DESKTOP):                 # aplikacja odinstalowana – sprzątamy
        for p in (USER_ICON, USER_DESKTOP):
            if os.path.exists(p):
                os.remove(p)
        return None
    dark = system_dark() if dark is None else dark
    src = paths.data("icons", "app-dark.svg" if dark else "app-light.svg")
    with open(src, "rb") as f:
        changed = _write_if_changed(USER_ICON, f.read())
    with open(SYSTEM_DESKTOP, encoding="utf-8") as f:
        lines = [(f"Icon={src}" if ln.startswith("Icon=") else ln) for ln in f.read().splitlines()]
    changed |= _write_if_changed(USER_DESKTOP, ("\n".join(lines) + "\n").encode())
    if changed and shutil.which("update-desktop-database"):
        os.system(f"update-desktop-database -q '{os.path.dirname(USER_DESKTOP)}' >/dev/null 2>&1")
    return "dark" if dark else "light"


def watch():
    """Autostart sesji: czeka na sygnał zmiany motywu i od razu podmienia ikonę (bez odpytywania)."""
    apply_icon()
    src = Gio.SettingsSchemaSource.get_default()
    if not (src and src.lookup("org.gnome.desktop.interface", True)):
        return
    s = Gio.Settings.new("org.gnome.desktop.interface")
    s.connect("changed::color-scheme", lambda *_: apply_icon())
    s.connect("changed::gtk-theme", lambda *_: apply_icon())
    GLib.MainLoop().run()


if __name__ == "__main__":
    watch() if "--watch" in sys.argv else print(apply_icon())
