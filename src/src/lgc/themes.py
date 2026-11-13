"""Motywy wyglądu: System (Adwaita), Aurora (jasny/ciemny według systemu – pastelowe szkło / zorza,
gradient fiolet → cyjan, poświata po najechaniu) i Studio Pro (ciemny, ergonomiczny: grafit, jeden
bursztynowy akcent). Kolory Adwaity nadpisywane na żywo w osobnym dostawcy CSS; libadwaita ≥ 1.6 czyta
zmienne CSS, starsze – @define-color."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk  # noqa: E402

THEMES = ("system", "aurora", "pro")

COLORS = {
    False: dict(window_bg="#f4f1ff", window_fg="#1f1a3a", view_bg="rgba(255,255,255,0.70)", view_fg="#1f1a3a",
                headerbar_bg="rgba(255,255,255,0.58)", headerbar_fg="#1f1a3a", sidebar_bg="rgba(255,255,255,0.30)",
                sidebar_fg="#1f1a3a", card_bg="rgba(255,255,255,0.75)", card_fg="#1f1a3a",
                popover_bg="#fbfaff", popover_fg="#1f1a3a", dialog_bg="#fbfaff", dialog_fg="#1f1a3a",
                accent_bg="#7c5cff", accent_fg="#ffffff", accent="#6d4dff"),
    True: dict(window_bg="#0c0e1a", window_fg="#ecebff", view_bg="rgba(255,255,255,0.03)", view_fg="#ecebff",
               headerbar_bg="rgba(255,255,255,0.04)", headerbar_fg="#ecebff", sidebar_bg="rgba(255,255,255,0.012)",
               sidebar_fg="#ecebff", card_bg="rgba(255,255,255,0.05)", card_fg="#ecebff",
               popover_bg="#161a2e", popover_fg="#ecebff", dialog_bg="#161a2e", dialog_fg="#ecebff",
               accent_bg="#8b5cf6", accent_fg="#ffffff", accent="#22d3ee"),
}

EXTRA = {
    False: """
window.background:not(.aurora-off) {
  background-image: linear-gradient(135deg, #f6f2ff 0%, #eef8ff 55%, #fff4f8 100%);
}
headerbar { box-shadow: inset 0 -1px alpha(#7c5cff, 0.12); }
.navigation-sidebar > row:selected, listview > row:selected, list.content > row:selected {
  background-image: linear-gradient(90deg, #7c5cff, #22b8e6); color: #ffffff;
  box-shadow: 0 6px 18px alpha(#7c5cff, 0.30);
}
.navigation-sidebar > row:hover:not(:selected), listview > row:hover:not(:selected) {
  background-color: #ffffff;
  box-shadow: 0 0 0 1.5px alpha(#7c5cff, 0.55), 0 8px 22px alpha(#7c5cff, 0.25);
}
button.suggested-action {
  background-image: linear-gradient(90deg, #7c5cff, #22b8e6); color: #ffffff;
  box-shadow: 0 6px 18px alpha(#7c5cff, 0.40);
}
""",
    True: """
window.background:not(.aurora-off) {
  background-image: radial-gradient(ellipse at 12% -5%, alpha(#22d3ee, 0.20), transparent 55%),
                    radial-gradient(ellipse at 100% 105%, alpha(#a855f7, 0.24), transparent 55%);
}
headerbar { box-shadow: inset 0 -1px alpha(#ffffff, 0.07); }
.navigation-sidebar > row:selected, listview > row:selected, list.content > row:selected {
  background-image: linear-gradient(90deg, alpha(#a855f7, 0.60), alpha(#22d3ee, 0.48)); color: #ffffff;
  box-shadow: 0 6px 18px alpha(#a855f7, 0.30);
}
.navigation-sidebar > row:hover:not(:selected), listview > row:hover:not(:selected) {
  background-color: alpha(#ffffff, 0.05);
  box-shadow: 0 0 0 1px alpha(#22d3ee, 0.55), 0 0 20px alpha(#22d3ee, 0.28);
}
button.suggested-action {
  background-image: linear-gradient(90deg, #a855f7, #22d3ee); color: #ffffff;
  box-shadow: 0 0 18px alpha(#a855f7, 0.45);
}
""",
}

COMMON = """
.navigation-sidebar > row, listview > row { border-radius: 11px; transition: box-shadow 150ms, background 150ms; }
.navigation-sidebar > row { margin: 1px 6px; }
"""


def _color_block(c):
    if (Adw.get_major_version(), Adw.get_minor_version()) >= (1, 6):
        return ":root {\n" + "".join(f"  --{k.replace('_', '-')}-color: {v};\n" for k, v in c.items()) + "}\n"
    return "".join(f"@define-color {k}_color {v};\n" for k, v in c.items())


PRO_COLORS = dict(window_bg="#1E1F22", window_fg="#E0E2E6", view_bg="#1A1B1E", view_fg="#E0E2E6",
                  headerbar_bg="#1A1B1E", headerbar_fg="#D4D7DD", sidebar_bg="#25272C", sidebar_fg="#E0E2E6",
                  card_bg="#25272C", card_fg="#E0E2E6", popover_bg="#2E3138", popover_fg="#E0E2E6",
                  dialog_bg="#2E3138", dialog_fg="#E0E2E6", accent_bg="#D99B26", accent_fg="#1A1B1E", accent="#D99B26")
PRO_EXTRA = """
window.background { background-image: none; font-feature-settings: "tnum"; }
headerbar { background: #1A1B1E; box-shadow: inset 0 -1px #25272C; }
.dim-label, .dimmed, label.subtitle { color: #8A8F98; opacity: 1; }
button.suggested-action { background-image: none; background-color: #D99B26; color: #1A1B1E; box-shadow: none; }
.boxed-list, .card { border: none; box-shadow: none; background-color: #25272C; border-radius: 10px; }
"""


def css_for(dark, extra=""):
    return _color_block(COLORS[dark]) + EXTRA[dark] + COMMON + extra


def css_pro():
    return _color_block(PRO_COLORS) + PRO_EXTRA


class Themes:
    """apply('system' | 'aurora' | 'pro'); po zmianie jasny/ciemny w systemie przelicza się sam.
    extra: dodatkowe reguły konkretnej aplikacji (np. bardziej przezroczysty pasek boczny)."""

    def __init__(self, extra=None):
        self.name = "system"
        self.extra = extra or {False: "", True: ""}
        self.provider = None
        Adw.StyleManager.get_default().connect("notify::dark", lambda *_: self._reload())

    def apply(self, name):
        self.name = name if name in THEMES else "system"
        self._reload()

    def _reload(self):
        display = Gdk.Display.get_default()
        if self.provider is not None:
            Gtk.StyleContext.remove_provider_for_display(display, self.provider)
            self.provider = None
        sm = Adw.StyleManager.get_default()
        if self.name == "pro":
            sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)        # Studio Pro jest zawsze ciemny
            css = css_pro()
        elif self.name == "aurora":
            sm.set_color_scheme(Adw.ColorScheme.DEFAULT)
            dark = sm.get_dark()
            css = css_for(dark, self.extra.get(dark, ""))
        else:
            sm.set_color_scheme(Adw.ColorScheme.DEFAULT)
            return
        self.provider = Gtk.CssProvider()
        if hasattr(self.provider, "load_from_string"):
            self.provider.load_from_string(css)
        else:
            self.provider.load_from_data(css, -1)
        Gtk.StyleContext.add_provider_for_display(display, self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
