"""Ustawienia: motyw, język, powiadomienia, start z systemem, zasobnik, sprawdzanie pisowni."""
import gi

gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Adw, GLib, Gtk, WebKit  # noqa: E402

from . import desktop  # noqa: E402
from .i18n import _, load_settings, save_settings  # noqa: E402

THEMES = ("system", "aurora", "pro")
LANGS = ("auto", "pl", "en")


class PrefsDialog(Adw.PreferencesDialog):
    def __init__(self, app):
        super().__init__(title=_("Preferences"))
        self.app = app
        cfg = load_settings()
        page = Adw.PreferencesPage()

        look = Adw.PreferencesGroup(title=_("Appearance"))
        self.theme = Adw.ComboRow(title=_("Theme"), subtitle=_("Window and menu colours; light or dark follows the system"),
                                  model=Gtk.StringList.new([_("System"), _("Aurora"), _("Studio Pro")]))
        self.theme.set_selected(THEMES.index(cfg["theme"]) if cfg["theme"] in THEMES else 0)
        self.theme.connect("notify::selected", self._on_theme)
        look.add(self.theme)
        page.add(look)

        gen = Adw.PreferencesGroup(title=_("General"))
        self.lang = Adw.ComboRow(title=_("Language"),
                                 model=Gtk.StringList.new([_("Automatic (system language)"), "Polski", "English"]))
        self.lang.set_selected(LANGS.index(cfg["language"]) if cfg["language"] in LANGS else 0)
        self.lang.connect("notify::selected", self._on_lang)
        gen.add(self.lang)
        for key, title, sub, cb in (
                ("notifications", _("Notifications"), _("Show new messages as GNOME notifications"), None),
                ("autostart", _("Start with the system"), _("In the background – only the tray icon"), desktop.set_autostart),
                ("close_to_tray", _("Keep running in the tray when the window is closed"), "", None),
                ("spellcheck", _("Spell checking (Polish + English)"), "", self._spell)):
            row = Adw.SwitchRow(title=title, subtitle=sub, active=bool(cfg[key]))
            row.connect("notify::active", lambda r, _p, key=key, cb=cb: self._on_switch(key, r.get_active(), cb))
            gen.add(row)
        page.add(gen)
        self.add(page)

    def _on_theme(self, row, _p):
        name = THEMES[row.get_selected()]
        self.app.activate_action("theme", GLib.Variant("s", name))

    def _on_lang(self, row, _p):
        save_settings(language=LANGS[row.get_selected()])
        if self.app.win:
            self.app.win.toast(_("Language change takes effect after restarting the app"))

    @staticmethod
    def _spell(on):
        WebKit.WebContext.get_default().set_spell_checking_enabled(on)

    @staticmethod
    def _on_switch(key, value, cb):
        save_settings(**{key: value})
        if cb:
            cb(value)
