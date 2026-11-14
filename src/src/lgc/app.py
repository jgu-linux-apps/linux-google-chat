"""Linux Google Chat – aplikacja: ekran startowy, zasobnik, licznik w docku, powiadomienia GNOME,
tryb Nie przeszkadzać, motywy, ustawienia, O programie."""
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import APP_ID, APP_NAME, VERSION, WEBSITE, desktop, i18n, paths  # noqa: E402
from .i18n import _, load_settings, save_settings  # noqa: E402
from .notify import Notifier  # noqa: E402
from .themes import Themes  # noqa: E402

CSS = """
window.lgc-splash { background: transparent; box-shadow: none; border-radius: 18px; outline: none; }
window.lgc-splash .lgc-splash-card { border-radius: 18px; padding: 28px 30px; min-width: 520px; min-height: 200px; color: #ffffff;
  background-color: #0c0e1a;
  background-image: radial-gradient(ellipse at 15% 0%, alpha(#22d3ee, 0.38), transparent 60%),
                    radial-gradient(ellipse at 100% 100%, alpha(#a855f7, 0.48), transparent 60%); }
.lgc-splash-kicker { font-size: 0.82em; letter-spacing: 0.3em; color: #a9a6d6; }
.lgc-splash-name { font-size: 2.1em; font-weight: 800; }
.lgc-splash-made { font-weight: 700; } .lgc-splash-sub { color: #b9b6e3; font-size: 0.85em; }
progressbar.lgc-splash-bar > trough { min-height: 4px; background: alpha(#ffffff, 0.12); border-radius: 2px; }
progressbar.lgc-splash-bar > trough > progress { min-height: 4px; border-radius: 2px;
  background-image: linear-gradient(to right, #22d3ee, #a855f7); }
"""


class ChatApp(Adw.Application):
    def __init__(self, hidden=False):
        super().__init__(application_id=APP_ID)
        self.hidden = hidden
        self.win = None
        self.splash = None
        self.tray = None
        self.badge = None
        self.notes = {}                 # tag powiadomienia -> WebKit.Notification (kliknięcie otwiera rozmowę)
        self.notifier = Notifier(APP_NAME, APP_ID, APP_ID, self._on_notif_click)
        cfg = load_settings()
        self.dnd = bool(cfg["dnd"])
        self.unread = 0
        self._tray_hint = False

    # ================================================================ start
    def do_startup(self):
        Adw.Application.do_startup(self)
        prov = Gtk.CssProvider()
        prov.load_from_string(CSS) if hasattr(prov, "load_from_string") else prov.load_from_data(CSS, -1)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)  # nad motywem (APPLICATION + 1)
        Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(paths.ICON_DIR)
        cfg = load_settings()
        self.look = Themes()
        self.look.apply(cfg["theme"])
        sm = Adw.StyleManager.get_default()
        sm.connect("notify::dark", lambda *_: self._sync_icons())
        self.badge = desktop.LauncherBadge()

        def add(name, cb, ptype=None, state=None):
            if state is not None:
                a = Gio.SimpleAction.new_stateful(name, GLib.VariantType.new(ptype) if ptype else None, state)
            else:
                a = Gio.SimpleAction.new(name, GLib.VariantType.new(ptype) if ptype else None)
            a.connect("activate", cb)
            self.add_action(a)
            return a
        add("show", lambda *_: self.show_window())
        add("quit", lambda *_: self.quit())
        add("preferences", lambda *_: self.show_prefs())
        add("about", lambda *_: self.show_about())
        add("theme", self._on_theme, "s", GLib.Variant("s", self.look.name))
        self.dnd_action = add("dnd", self._on_dnd, None, GLib.Variant("b", self.dnd))
        add("zoom-in", lambda *_: self.win and self.win.zoom(+1))
        add("zoom-out", lambda *_: self.win and self.win.zoom(-1))
        add("zoom-reset", lambda *_: self.win and self.win.zoom(0))
        for action, accels in (("app.quit", ["<Control>q"]), ("app.preferences", ["<Control>comma"]),
                               ("app.zoom-in", ["<Control>plus", "<Control>equal"]),
                               ("app.zoom-out", ["<Control>minus"]), ("app.zoom-reset", ["<Control>0"])):
            self.set_accels_for_action(action, accels)
        self._make_tray()
        self._sync_icons()
        self.hold()                       # działa dalej w zasobniku po zamknięciu okna

    def do_activate(self):
        if self.win is None:
            from .window import ChatWindow
            self.win = ChatWindow(self)
            refresh = Gtk.ShortcutController()
            refresh.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string("F5"),
                                                  Gtk.CallbackAction.new(lambda *_: (self.win.web.reload(), True)[1])))
            self.win.add_controller(refresh)
            self.win.update_subtitle()
            if self.hidden:
                self.hidden = False       # start w tle: okno ładuje Chat, ale się nie pokazuje
                return
            self._show_splash()
            GLib.timeout_add(6000, self._splash_done)      # najpóźniej po 6 s, nawet bez sieci
            return
        self.show_window()

    # ================================================================ ekran startowy
    def _show_splash(self):
        w = Gtk.Window(decorated=False, resizable=False, application=self)
        # bez klasy „background”: reguły motywu (window.background) malowałyby tło pod zaokrągloną kartą (białe rogi)
        w.remove_css_class("background")
        w.add_css_class("lgc-splash")
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("lgc-splash-card")
        top = Gtk.Box()
        names = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True)
        k = Gtk.Label(label="LINUX", xalign=0)
        k.add_css_class("lgc-splash-kicker")
        n = Gtk.Label(label="GOOGLE CHAT", xalign=0)
        n.add_css_class("lgc-splash-name")
        names.append(k)
        names.append(n)
        made = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.START)
        m1 = Gtk.Label(label=_("made by: JGu"), xalign=1)
        m1.add_css_class("lgc-splash-made")
        m2 = Gtk.Label(label=_("Supported by Claude"), xalign=1)
        m2.add_css_class("lgc-splash-sub")
        made.append(m1)
        made.append(m2)
        top.append(names)
        top.append(made)
        card.append(top)
        card.append(Gtk.Box(vexpand=True))
        meta = Gtk.Box()
        st = Gtk.Label(label=_("Connecting to Google Chat…"), xalign=0, hexpand=True)
        st.add_css_class("lgc-splash-sub")
        v = Gtk.Label(label=f"v{VERSION}")
        v.add_css_class("lgc-splash-sub")
        meta.append(st)
        meta.append(v)
        card.append(meta)
        self.splash_bar = Gtk.ProgressBar(margin_top=8)
        self.splash_bar.add_css_class("lgc-splash-bar")
        card.append(self.splash_bar)
        w.set_child(card)
        self.splash = w
        w.present()
        GLib.timeout_add(80, self._splash_pulse)

    def _splash_pulse(self):
        if self.splash is None:
            return False
        self.splash_bar.set_fraction(min(0.95, self.splash_bar.get_fraction() + 0.03))
        return True

    def _splash_done(self):
        if self.splash is not None:
            self.splash.destroy()
            self.splash = None
            self.show_window()
        return False

    def page_ready(self):
        """Pierwsze pełne załadowanie strony – chowamy ekran startowy."""
        if self.splash is not None:
            GLib.timeout_add(250, self._splash_done)

    # ================================================================ okno i zasobnik
    def show_window(self, token=None):
        if self.win is None:
            self.activate()
            return
        self.notifier.close("tray-hint")  # okno znów widoczne: podpowiedź o zasobniku jest już zbędna
        if token:
            self.win.set_startup_id(token)   # token z kliknięcia w powiadomienie: okno dostaje fokus pod Waylandem
        self.win.set_visible(True)
        self.win.present()

    def on_window_close(self):
        cfg = load_settings()
        if cfg["close_to_tray"] and self.tray_available():
            self.win.set_visible(False)
            if not self._tray_hint:
                self._tray_hint = True
                # przez notify.py jak wiadomości: kliknięcie otwiera okno i zamyka podpowiedź
                self.notifier.show("tray-hint", _("Linux Google Chat keeps running in the tray"),
                                   _("Click the tray icon to open the window again."))
            return True
        self.quit()
        return True

    def tray_available(self):
        if self.tray is None or self.tray.bus is None:
            return False
        try:
            r = self.tray.bus.call_sync("org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
                                        "NameHasOwner", GLib.Variant("(s)", ("org.kde.StatusNotifierWatcher",)),
                                        None, Gio.DBusCallFlags.NONE, 1000, None)
            return bool(r.unpack()[0])
        except GLib.Error:
            return False

    def _tray_items(self):
        show = _("Show Chat") + (f"  ({self.unread})" if self.unread else "")
        dnd = ("✓ " if self.dnd else "") + _("Do Not Disturb")
        # identyfikatory muszą być > 0: 0 to w DBusMenu korzeń całego menu (separator z id 0 = menu zawierające
        # samo siebie -> rozszerzenie AppIndicator w powłoce GNOME zapętlało się i zawieszało pulpit)
        return [(1, show, self.show_window), (2, dnd, lambda: self.dnd_action.activate(None)), (3, None, None),
                (4, _("Preferences"), self.show_prefs), (5, _("Quit"), self.quit)]

    def _make_tray(self):
        try:
            from .tray import Tray
            self.tray = Tray(APP_ID, APP_NAME, desktop.tray_icon_name(self._dark(), False),
                             self.show_window, self._tray_items())
        except Exception as e:  # noqa: BLE001
            print("tray:", e)
            self.tray = None

    def _dark(self):
        return Adw.StyleManager.get_default().get_dark()

    def _sync_icons(self):
        dark = self._dark()
        Gtk.Window.set_default_icon_name(APP_ID)
        if self.tray:
            self.tray.set_icon(desktop.tray_icon_name(dark, self.unread > 0))
        try:
            desktop.apply_icon()          # dock i menu aplikacji – według motywu systemu
        except Exception as e:  # noqa: BLE001
            print("icon:", e)

    def set_unread(self, n):
        if n == self.unread:
            return
        self.unread = n
        self.badge.set(n)
        if n == 0:
            self._withdraw_all()          # wszystko przeczytane: powiadomienia znikają z GNOME
        if self.tray:
            self.tray.set_icon(desktop.tray_icon_name(self._dark(), n > 0))
            self.tray.set_tooltip(APP_NAME + (f" – {_('%d unread') % n}" if n else ""))
            self.tray.set_items(self._tray_items())

    # ================================================================ powiadomienia
    def web_notification(self, note):
        if self.dnd or not load_settings()["notifications"]:
            return
        tag = f"chat-{note.get_id()}"
        self.notes[tag] = note
        if len(self.notes) > 50:
            self._withdraw(next(iter(self.notes)))
        self.notifier.show(tag, note.get_title() or "Chat", note.get_body() or "")
        # strona Chat sama zamyka powiadomienie, gdy wiadomość jest przeczytana – wtedy znika też z GNOME
        note.connect("closed", lambda *_a, tag=tag: self._withdraw(tag))

    def _withdraw(self, tag):
        self.notes.pop(tag, None)
        self.notifier.close(tag)

    def _withdraw_all(self):
        for tag in set(self.notes) | set(self.notifier.tags()):
            self._withdraw(tag)

    def _on_notif_click(self, tag, token):
        self.show_window(token)
        note = self.notes.pop(tag, None)
        if note is not None:
            note.clicked()                # strona Chat otwiera właściwą rozmowę
        # notify.py zamyka samo powiadomienie w GNOME

    def _on_dnd(self, action, _v):
        self.dnd = not action.get_state().get_boolean()
        action.set_state(GLib.Variant("b", self.dnd))
        save_settings(dnd=self.dnd)
        if self.win:
            self.win.update_subtitle()
            if self.dnd:
                self.win.toast(_("Do Not Disturb is on – notifications are muted"))
        if self.tray:
            self.tray.set_items(self._tray_items())

    def _on_theme(self, action, v):
        action.set_state(v)
        self.look.apply(v.get_string())
        save_settings(theme=v.get_string())

    # ================================================================ okna dialogowe
    def show_about(self):
        d = Adw.AboutDialog(application_name=APP_NAME, application_icon=APP_ID, version=VERSION,
                            developer_name=_("made by: JGu") + "\n" + _("Supported by Claude"),
                            comments=_("Desktop app for Google Chat on Ubuntu") + "\n"
                            + _("Unofficial – not affiliated with Google."),
                            website=WEBSITE, license_type=Gtk.License.CUSTOM,
                            license="Freeware License (No Modifications) – see LICENSE")
        d.set_developers(["JGu"])
        d.add_credit_section("Supported by", ["Claude (Anthropic)"])
        d.present(self.win)

    def show_prefs(self):
        from .prefs import PrefsDialog
        self.show_window()
        PrefsDialog(self).present(self.win)


def main():
    hidden = "--hidden" in sys.argv
    argv = [a for a in sys.argv if a != "--hidden"]
    return ChatApp(hidden=hidden).run(argv)


if __name__ == "__main__":
    sys.exit(main())
